import os
import datetime
import jwt
import time
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response, stream_with_context
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "0KjsCksm3S9uqknLecDIfE3f8HcXgwZC9QSw-82h32BV6Vo4TPDNL_CPidwY1P_lK-YSrltS_308vuAJAzXGWA"
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov'}
app.config['ZONE_THRESHOLDS'] = {}

# Initialize database
def init_db():
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        ''')
        # Add a column to store the latest JWT per user (idempotent)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN user_jwt TEXT;')
        except Exception:
            pass
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zones (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                video_path TEXT NOT NULL,
                label TEXT NOT NULL,
                top_left_x INTEGER,
                top_left_y INTEGER,
                bottom_right_x INTEGER,
                bottom_right_y INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        # NEW: Create table for user profile details
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                dob TEXT,
                age INTEGER,
                place TEXT,
                gender TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        cursor.execute('''
            DROP TABLE IF EXISTS user_tokens;
        ''')
        conn.commit()

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# New way to initialize the database
with app.app_context():
    init_db()
    
# --- NEW: User Profile Route ---
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    with sqlite3.connect('video_zone.db') as conn:
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        cursor = conn.cursor()

        if request.method == 'POST':
            dob = request.form.get('dob')
            age = request.form.get('age')
            place = request.form.get('place')
            gender = request.form.get('gender')
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles (user_id, dob, age, place, gender)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, dob, age, place, gender))
            
            conn.commit()
            flash('Profile updated successfully!')
            return redirect(url_for('profile'))

        # For GET requests
        cursor.execute('SELECT username, email FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()

        cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        profile_data = cursor.fetchone()
        
        # If no profile exists yet, create an empty object to avoid errors in the template
        if profile_data is None:
            profile_data = {}

    return render_template('profile.html', user=user_data, profile=profile_data, username=session['username'])


# --- Tracker Service (Milestone 3) ---
tracker = None
def get_tracker():
    global tracker
    if tracker is None:
        from tracker_service import RealtimeTracker
        tracker = RealtimeTracker()
    return tracker

# --- (CHANGE 1) NEW: PRE-LOAD THE MODEL ON STARTUP ---
print("Loading tracking model, please wait...")
try:
    get_tracker().warmup()
    print("Tracking model loaded successfully.")
except Exception as e:
    print(f"Error loading model during startup: {e}")
# --- END PRE-LOADING ---


# --- Zone Manipulation Tracking Preview (DeepSORT IDs for uploaded video) ---
@app.route('/zm_start_tracking', methods=['POST'])
def zm_start_tracking():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    source = data.get('video_path')
    if not source:
        return jsonify({'error': 'Missing video_path'}), 400
    # convert static url to file path if needed
    if isinstance(source, str):
        # Accept full URL, path, or /static/... URL
        try:
            from urllib.parse import urlparse
            parsed = urlparse(source)
            if parsed.scheme in ('http', 'https'):
                # Use only the path portion for local static files
                source = parsed.path
        except Exception:
            pass
        if source.startswith('/static/'):
            rel_path = source.lstrip('/')
            abs_path = os.path.join(app.root_path, rel_path)
            source = abs_path
        elif not os.path.isabs(source):
            # Make relative paths absolute from app root
            source = os.path.join(app.root_path, source)
    # Validate file exists
    if not os.path.exists(source):
        return jsonify({'error': f'Video not found at {source}'}), 400
    
    # --- (REMOVED) Model is already pre-loaded ---
    
    zones = _load_user_zones()
    get_tracker().start(source, zones)
    return jsonify({'message': 'Tracking started'})

@app.route('/zm_stop_tracking', methods=['POST'])
def zm_stop_tracking():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    get_tracker().stop()
    return jsonify({'message': 'Tracking stopped'})

@app.route('/zm_feed')
def zm_feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    def gen():
        while True:
            frame = get_tracker().get_latest_frame()
            if frame is None:
                time.sleep(0.03)
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- User Authentication Routes ---
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not username or not password or not email:
            flash('Please fill out all fields.')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('register.html')

        with sqlite3.connect('video_zone.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE LOWER(username) = ?', (username.lower(),))
            user = cursor.fetchone()
            if user:
                flash('Username already exists.')
                return render_template('register.html')

            cursor.execute('SELECT * FROM users WHERE LOWER(email) = ?', (email.lower(),))
            user_email = cursor.fetchone()
            if user_email:
                flash('Email address already registered.')
                return render_template('register.html')

            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_password))
            conn.commit()

        flash('Registration successful. You can login now.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with sqlite3.connect('video_zone.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user[3], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                # Generate a JWT and store alongside password hash (in users.user_jwt)
                try:
                    payload = {
                        'sub': user[0],
                        'username': user[1],
                        'iat': datetime.datetime.utcnow(),
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
                    }
                    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
                    cursor.execute('UPDATE users SET user_jwt = ? WHERE id = ?', (token, user[0]))
                    conn.commit()
                except Exception:
                    pass
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username/password.')
                return render_template('login.html')
                
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# --- Dashboard & Video/Zone Management Routes ---
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # --- (CHANGE 2) PERFORMANCE OPTIMIZATION (REMOVED) ---
    # The model is now loaded once on startup,
    # so we don't need to load it here anymore.
    # --- END OPTIMIZATION ---
        
    return render_template('dashboard.html', username=session['username'])

@app.route('/live')
def live_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # --- (CHANGE 3) PERFORMANCE OPTIMIZATION (REMOVED) ---
    # The model is now loaded once on startup,
    # so we don't need to load it here anymore.
    # --- END OPTIMIZATION ---
    
    return render_template('live.html', username=session['username'])

@app.route('/upload-video', methods=['POST'])
def upload_video():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
        
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            return jsonify({
                'message': 'Video uploaded successfully',
                'video_path': url_for('static', filename=f'uploads/{filename}')
            })
        except Exception as e:
            return jsonify({'error': f'File upload failed: {str(e)}'}), 500
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/save_zone', methods=['POST'])
def save_zone():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json or {}
    label = data.get('label')
    video_path = data.get('video_path')
    top_left_x = data.get('topLeftX')
    top_left_y = data.get('topLeftY')
    bottom_right_x = data.get('bottomRightX')
    bottom_right_y = data.get('bottomRightY')

    if not all([label, video_path, top_left_x, top_left_y, bottom_right_x, bottom_right_y]):
        return jsonify({'error': 'Missing zone data'}), 400
        
    user_id = session['user_id']
    
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO zones (user_id, video_path, label, top_left_x, top_left_y, bottom_right_x, bottom_right_y)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        ''', (user_id, video_path, label, top_left_x, top_left_y, bottom_right_x, bottom_right_y))
        conn.commit()
    
    return jsonify({'message': 'Zone saved successfully'}), 201

@app.route('/get_zones', methods=['GET'])
def get_zones():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT label, top_left_x, top_left_y, bottom_right_x, bottom_right_y FROM zones WHERE user_id = ?', (user_id,))
        zones = cursor.fetchall()
    
    zone_list = []
    for zone in zones:
        zone_list.append({
            'label': zone[0],
            'topLeftX': zone[1],
            'topLeftY': zone[2],
            'bottomRightX': zone[3],
            'bottomRightY': zone[4]
        })
    return jsonify(zone_list)

@app.route('/set_thresholds', methods=['POST'])
def set_thresholds():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    user_id = session['user_id']
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zone_thresholds (
                user_id INTEGER,
                zone_label TEXT,
                threshold INTEGER,
                PRIMARY KEY (user_id, zone_label)
            );
        ''')
        for label, thr in data.items():
            try:
                thr_int = int(thr)
            except Exception:
                continue
            cursor.execute('INSERT OR REPLACE INTO zone_thresholds (user_id, zone_label, threshold) VALUES (?, ?, ?)', (user_id, label, thr_int))
        conn.commit()
    return jsonify({'message': 'Thresholds saved'})

@app.route('/get_thresholds', methods=['GET'])
def get_thresholds():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zone_thresholds (
                user_id INTEGER,
                zone_label TEXT,
                threshold INTEGER,
                PRIMARY KEY (user_id, zone_label)
            );
        ''')
        cursor.execute('SELECT zone_label, threshold FROM zone_thresholds WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
    return jsonify({label: thr for (label, thr) in rows})

@app.route('/delete_zone', methods=['POST'])
def delete_zone():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    # Safely parse JSON body; request.json can be None if content-type is missing or body empty
    data = request.get_json(silent=True) or {}
    label = data.get('label')
    
    if not label:
        return jsonify({'error': 'Missing zone label'}), 400
        
    user_id = session['user_id']
    
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM zones WHERE user_id = ? AND label = ?', (user_id, label))
        conn.commit()
        if cursor.rowcount > 0:
            # Update tracker zones if running so live/zm views reflect deletion immediately
            try:
                updated_zones = _load_user_zones()
                get_tracker().update_zones(updated_zones)
            except Exception:
                pass
            return jsonify({'message': 'Zone deleted successfully'}), 200
        else:
            return jsonify({'error': 'Zone not found'}), 404

@app.route('/edit_zone', methods=['POST'])
def edit_zone():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json or {}
    old_label = data.get('old_label')
    new_label = data.get('new_label')
    
    if not old_label or not new_label:
        return jsonify({'error': 'Missing old or new label'}), 400
        
    user_id = session['user_id']
    
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE zones SET label = ? WHERE user_id = ? AND label = ?', (new_label, user_id, old_label))
        conn.commit()
        if cursor.rowcount > 0:
            # Refresh tracker zones if running so live/zm views reflect new names immediately
            try:
                updated_zones = _load_user_zones()
                get_tracker().update_zones(updated_zones)
            except Exception:
                pass
            return jsonify({'message': 'Zone updated successfully'}), 200
        else:
            return jsonify({'error': 'Zone not found or no changes made'}), 404

# --- Live Streaming & Stats (Milestone 3) ---
def _load_user_zones() -> list:
    if 'user_id' not in session:
        return []
    user_id = session['user_id']
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT label, top_left_x, top_left_y, bottom_right_x, bottom_right_y FROM zones WHERE user_id = ?', (user_id,))
        zones = cursor.fetchall()
    return [
        {
            'label': z[0],
            'topLeftX': z[1],
            'topLeftY': z[2],
            'bottomRightX': z[3],
            'bottomRightY': z[4]
        } for z in zones
    ]

@app.route('/start_stream', methods=['POST'])
def start_stream():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    body = request.json or {}
    source = body.get('source')
    zones = _load_user_zones()
    # If source not provided, try to infer from latest saved zone video (avoid webcam)
    if not source:
        with sqlite3.connect('video_zone.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT video_path FROM zones WHERE user_id = ? ORDER BY id DESC LIMIT 1', (session['user_id'],))
            row = cursor.fetchone()
            if row and row[0] and row[0] != 'webcam_feed':
                source = row[0]
    if not source:
        return jsonify({'error': 'No source available. Please upload a video and create zones first.'}), 400
    # If the stored path is a Flask static URL like /static/uploads/file.mp4, convert to local file path
    if isinstance(source, str) and source.startswith('/static/'):
        source = os.path.normpath(source.lstrip('/'))
    src_val = 0 if source == 'webcam' else source
    get_tracker().start(src_val, zones)
    return jsonify({'message': 'Stream started'})

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    get_tracker().stop()
    return jsonify({'message': 'Stream stopped'})

@app.route('/video_feed')
def video_feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    def gen():
        while True:
            frame = get_tracker().get_latest_frame()
            if frame is None:
                time.sleep(0.03)
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats_stream')
def stats_stream():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    @stream_with_context
    def event_stream():
        import json, time as _t
        while True:
            counts = get_tracker().get_latest_counts()
            # pull thresholds from DB for persistence
            thresholds = {}
            try:
                with sqlite3.connect('video_zone.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT zone_label, threshold FROM zone_thresholds WHERE user_id = ?', (session['user_id'],))
                    thresholds = {row[0]: row[1] for row in cursor.fetchall()}
            except Exception:
                pass
            payload = {'counts': counts, 'thresholds': thresholds}
            yield f"data: {json.dumps(payload)}\n\n"
            _t.sleep(0.5)

    return Response(event_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    # This check ensures the folder exists when the app starts
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)