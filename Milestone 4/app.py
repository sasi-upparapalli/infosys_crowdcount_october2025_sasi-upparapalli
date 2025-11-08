import os
import datetime
import jwt
import time
import sqlite3
import io
import csv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    Response,
    stream_with_context,
    make_response,
    send_file
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.secret_key = "0KjsCksm3S9uqknLecDIfE3f8HcXgwZC9QSw-82h32BV6Vo4TPDNL_CPidwY1P_lK-YSrltS_308vuAJAzXGWA"
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov'}
app.config['ZONE_THRESHOLDS'] = {}

# ============ MILESTONE 4: ADMIN & LOGGING CONFIGURATION ============
ADMIN_ROLE = 'admin'
USER_ROLE = 'user'

# ========================================================================


def init_db():
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            );
        ''')
        
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN user_jwt TEXT;')
        except Exception:
            pass
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "user";')
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
        
        # MILESTONE 4: Activity Logging Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                details TEXT,
                ip_address TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        
        # MILESTONE 4: Cameras Table (for future IP camera integration)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cameras (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                location TEXT,
                status TEXT DEFAULT 'inactive',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')
        
        cursor.execute('''
            DROP TABLE IF EXISTS user_tokens;
        ''')
        conn.commit()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ============ MILESTONE 4: LOGGING UTILITY FUNCTION ============
def log_activity(user_id, action, entity_type=None, entity_id=None, details=None):
    """Log user activity to database"""
    try:
        ip_address = request.remote_addr if request else None
        with sqlite3.connect('video_zone.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, action, entity_type, entity_id, details, ip_address))
            conn.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")

def is_admin(user_id):
    """Check if user has admin role"""
    try:
        with sqlite3.connect('video_zone.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            return result and result[0] == ADMIN_ROLE
    except Exception:
        return False

def admin_required(f):
    """Decorator to check admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.')
            return redirect(url_for('login'))
        if not is_admin(session['user_id']):
            flash('You do not have admin access.')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ===================================================================

# New way to initialize the database
with app.app_context():
    init_db()
    
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
        try:
            from urllib.parse import urlparse
            parsed = urlparse(source)
            if parsed.scheme in ('http', 'https'):
                source = parsed.path
        except Exception:
            pass
        if source.startswith('/static/'):
            rel_path = source.lstrip('/')
            abs_path = os.path.join(app.root_path, rel_path)
            source = abs_path
        elif not os.path.isabs(source):
            source = os.path.join(app.root_path, source)
    # Validate file exists
    if not os.path.exists(source):
        return jsonify({'error': f'Video not found at {source}'}), 400
    
    zones = _load_user_zones()
    get_tracker().start(source, zones)
    
    # MILESTONE 4: Log the activity
    log_activity(session['user_id'], 'started_tracking', 'video', None, f'Started tracking on {source}')
    
    return jsonify({'message': 'Tracking started'})

@app.route('/zm_stop_tracking', methods=['POST'])
def zm_stop_tracking():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    get_tracker().stop()
    
    # MILESTONE 4: Log the activity
    log_activity(session['user_id'], 'stopped_tracking', 'video', None, 'Stopped tracking')
    
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
            cursor.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)', 
                          (username, email, hashed_password, USER_ROLE))
            conn.commit()
            
            # MILESTONE 4: Log registration
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            new_user_id = cursor.fetchone()[0]
            log_activity(new_user_id, 'registered', 'user', new_user_id, f'User registered: {username}')

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
                session['role'] = user[5] if len(user) > 5 else USER_ROLE
                
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
                
                # MILESTONE 4: Log login
                log_activity(user[0], 'login', 'user', user[0], f'User logged in')
                
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username/password.')
                return render_template('login.html')
                
    return render_template('login.html')

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_activity(user_id, 'logout', 'user', user_id, 'User logged out')
    
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# --- Dashboard & Video/Zone Management Routes ---
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    return render_template('dashboard.html', username=session['username'])

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    with sqlite3.connect('video_zone.db') as conn:
        conn.row_factory = sqlite3.Row
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
            log_activity(user_id, 'updated_profile', 'profile', user_id, 'Updated profile information')
            flash('Profile updated successfully!')
            return redirect(url_for('profile'))

        cursor.execute('SELECT username, email FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()

        cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        profile_data = cursor.fetchone()
        
        if profile_data is None:
            profile_data = {}

    return render_template('profile.html', user=user_data, profile=profile_data, username=session['username'])

@app.route('/live')
def live_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
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
            
            log_activity(session['user_id'], 'uploaded_video', 'video', None, f'Uploaded video: {filename}')
            
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
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, video_path, label, top_left_x, top_left_y, bottom_right_x, bottom_right_y))
        conn.commit()
        zone_id = cursor.lastrowid
    
    log_activity(user_id, 'created_zone', 'zone', zone_id, f'Created zone: {label}')
    
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
            )
        ''')
        for label, thr in data.items():
            try:
                thr_int = int(thr)
            except Exception:
                continue
            cursor.execute('INSERT OR REPLACE INTO zone_thresholds (user_id, zone_label, threshold) VALUES (?, ?, ?)', (user_id, label, thr_int))
        conn.commit()
    
    log_activity(user_id, 'updated_thresholds', 'zone', None, f'Updated zone thresholds')
    
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
            )
        ''')
        cursor.execute('SELECT zone_label, threshold FROM zone_thresholds WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
    return jsonify({label: thr for (label, thr) in rows})

@app.route('/delete_zone', methods=['POST'])
def delete_zone():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
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
            try:
                updated_zones = _load_user_zones()
                get_tracker().update_zones(updated_zones)
            except Exception:
                pass
            
            log_activity(user_id, 'deleted_zone', 'zone', None, f'Deleted zone: {label}')
            
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
            try:
                updated_zones = _load_user_zones()
                get_tracker().update_zones(updated_zones)
            except Exception:
                pass
            
            log_activity(user_id, 'updated_zone', 'zone', None, f'Renamed zone from {old_label} to {new_label}')
            
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
    if not source:
        with sqlite3.connect('video_zone.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT video_path FROM zones WHERE user_id = ? ORDER BY id DESC LIMIT 1', (session['user_id'],))
            row = cursor.fetchone()
            if row and row[0] and row[0] != 'webcam_feed':
                source = row[0]
    if not source:
        return jsonify({'error': 'No source available. Please upload a video and create zones first.'}), 400
    if isinstance(source, str) and source.startswith('/static/'):
        source = os.path.normpath(source.lstrip('/'))
    src_val = 0 if source == 'webcam' else source
    get_tracker().start(src_val, zones)
    
    log_activity(session['user_id'], 'started_stream', 'stream', None, f'Started live stream')
    
    return jsonify({'message': 'Stream started'})

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    get_tracker().stop()
    
    log_activity(session['user_id'], 'stopped_stream', 'stream', None, 'Stopped live stream')
    
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

# ============================================================================
# MILESTONE 4: ADMIN PANEL ROUTES
# ============================================================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin Dashboard"""
    user_id = session['user_id']
    
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        
        # Get total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Get total zones
        cursor.execute('SELECT COUNT(*) FROM zones')
        total_zones = cursor.fetchone()[0]
        
        # Get total cameras
        cursor.execute('SELECT COUNT(*) FROM cameras')
        total_cameras = cursor.fetchone()[0]
        
        # Get recent activity
        cursor.execute('''
            SELECT u.username, a.action, a.entity_type, a.timestamp 
            FROM activity_logs a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.timestamp DESC
            LIMIT 10
        ''')
        recent_activities = cursor.fetchall()
    
    log_activity(user_id, 'accessed_admin_panel', 'admin', None, 'Accessed admin dashboard')
    
    return render_template('admin_dashboard.html', 
                          username=session['username'],
                          total_users=total_users,
                          total_zones=total_zones,
                          total_cameras=total_cameras,
                          recent_activities=recent_activities)

@app.route('/admin/users')
@admin_required
def admin_users():
    """Manage Users"""
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, role FROM users')
        users = cursor.fetchall()
    
    log_activity(session['user_id'], 'viewed_users', 'admin', None, 'Viewed users list')
    
    return render_template('admin_users.html', username=session['username'], users=users)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    """Edit User"""
    if request.method == 'POST':
        role = request.form.get('role')
        
        if role not in [ADMIN_ROLE, USER_ROLE]:
            flash('Invalid role selected.')
            return redirect(url_for('admin_users'))
        
        with sqlite3.connect('video_zone.db') as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
            conn.commit()
        
        log_activity(session['user_id'], 'updated_user_role', 'user', user_id, f'Changed role to {role}')
        flash(f'User role updated to {role}.')
        return redirect(url_for('admin_users'))
    
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, role FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
    
    if not user:
        flash('User not found.')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_edit_user.html', username=session['username'], user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Delete User"""
    # Prevent self-deletion
    if user_id == session['user_id']:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
    
    log_activity(session['user_id'], 'deleted_user', 'user', user_id, 'Deleted user account')
    
    return jsonify({'message': 'User deleted successfully'})


@app.route('/admin/zones')
@admin_required
def admin_zones():
    """Manage All Zones"""
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT z.id, z.label, z.video_path, u.username
            FROM zones z
            JOIN users u ON z.user_id = u.id
            ORDER BY z.id DESC
        ''')
        zones = cursor.fetchall()
    
    log_activity(session['user_id'], 'viewed_zones', 'admin', None, 'Viewed all zones')
    
    return render_template('admin_zones.html', username=session['username'], zones=zones)

@app.route('/admin/cameras')
@admin_required
def admin_cameras():
    """Manage Cameras"""
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.name, c.url, c.location, c.status, u.username
            FROM cameras c
            JOIN users u ON c.user_id = u.id
            ORDER BY c.id DESC
        ''')
        cameras = cursor.fetchall()
    
    log_activity(session['user_id'], 'viewed_cameras', 'admin', None, 'Viewed all cameras')
    
    return render_template('admin_cameras.html', username=session['username'], cameras=cameras)

@app.route('/admin/cameras/add', methods=['GET', 'POST'])
@admin_required
def admin_add_camera():
    """Add Camera"""
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url')
        location = request.form.get('location')
        user_id = request.form.get('user_id')
        
        if not all([name, url, user_id]):
            flash('Please fill in all required fields.')
            return redirect(url_for('admin_add_camera'))
        
        with sqlite3.connect('video_zone.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cameras (user_id, name, url, location, status)
                VALUES (?, ?, ?, ?, 'inactive')
            ''', (user_id, name, url, location))
            conn.commit()
            camera_id = cursor.lastrowid
        
        log_activity(session['user_id'], 'created_camera', 'camera', camera_id, f'Added camera: {name}')
        flash('Camera added successfully.')
        return redirect(url_for('admin_cameras'))
    
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username FROM users')
        users = cursor.fetchall()
    
    return render_template('admin_add_camera.html', username=session['username'], users=users)

@app.route('/admin/activity-log')
@admin_required
def admin_activity_log():
    """View Activity Logs"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM activity_logs')
        total = cursor.fetchone()[0]
        
        # Get paginated logs
        cursor.execute('''
            SELECT a.id, u.username, a.action, a.entity_type, a.details, a.ip_address, a.timestamp
            FROM activity_logs a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.timestamp DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        logs = cursor.fetchall()
    
    total_pages = (total + per_page - 1) // per_page
    
    log_activity(session['user_id'], 'viewed_activity_log', 'admin', None, 'Viewed activity logs')
    
    return render_template('admin_activity_log.html', 
                          username=session['username'],
                          logs=logs,
                          page=page,
                          total_pages=total_pages)
# --- Export Logs as CSV ---
@app.route('/admin/export-logs/csv')
@admin_required
def export_logs_csv():
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, u.username, a.action, a.entity_type, a.entity_id, a.details, a.ip_address, a.timestamp
            FROM activity_logs a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.timestamp DESC
        ''')
        logs = cursor.fetchall()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Username', 'Action', 'Entity Type', 'Entity ID', 'Details', 'IP Address', 'Timestamp'])
    cw.writerows(logs)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=activity_logs.csv"
    output.headers["Content-type"] = "text/csv"
    return output

# --- Export Logs as PDF ---
@app.route('/admin/export-logs/pdf')
@admin_required
def export_logs_pdf():
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        flash("PDF export requires 'reportlab' package. Please install it.")
        return redirect(url_for('admin_activity_log'))

    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, u.username, a.action, a.entity_type, a.entity_id, a.details, a.ip_address, a.timestamp
            FROM activity_logs a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.timestamp DESC
        ''')
        logs = cursor.fetchall()

    output = io.BytesIO()
    p = canvas.Canvas(output, pagesize=letter)
    width, height = letter
    y = height - 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Activity Logs Export")
    y -= 30
    p.setFont("Helvetica", 9)

    header = ['ID', 'Username', 'Action', 'Entity Type', 'Entity ID', 'Details', 'IP Address', 'Timestamp']
    x_positions = [50, 80, 140, 210, 280, 340, 440, 520]

    # Draw headers
    for i, header_text in enumerate(header):
        p.drawString(x_positions[i], y, header_text)
    y -= 20

    # Draw data rows
    for row in logs:
        if y < 50:  # create new page if near bottom
            p.showPage()
            y = height - 40
            p.setFont("Helvetica", 9)
        for i, item in enumerate(row):
            text = str(item)
            if len(text) > 20:
                text = text[:17] + "..."
            p.drawString(x_positions[i], y, text)
        y -= 15

    p.save()
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="activity_logs.pdf", mimetype='application/pdf')

@app.route('/admin/api/activity-stats')
@admin_required
def admin_activity_stats():
    """Get Activity Statistics (JSON)"""
    with sqlite3.connect('video_zone.db') as conn:
        cursor = conn.cursor()
        
        # Actions count
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM activity_logs
            GROUP BY action
        ''')
        action_stats = dict(cursor.fetchall())
        
        # Users count
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        # Zones count
        cursor.execute('SELECT COUNT(*) FROM zones')
        zone_count = cursor.fetchone()[0]
    
    return jsonify({
        'action_stats': action_stats,
        'user_count': user_count,
        'zone_count': zone_count
    })

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
