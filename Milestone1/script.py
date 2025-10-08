from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
import hashlib
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app, supports_credentials=True)
DATABASE = 'crowdcount.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    admin_password = hashlib.sha256('password123'.encode()).hexdigest()
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, email, password_hash)
        VALUES (?, ?, ?)
    """, ('admin', 'admin@crowdcount.com', admin_password))
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        if not all([username, email, password]):
            return jsonify({'error': 'All fields are required'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ? OR username = ?', (email, username))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'User already exists with this email or username'}), 409
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        """, (username, email, password_hash))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        session['user_id'] = user_id
        session['username'] = username
        return jsonify({'message': 'Registration successful','user': {'id': user_id,'username': username,'email': email}}), 201
    except Exception as e:
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        if not all([email, password]):
            return jsonify({'error': 'Email and password are required'}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        password_hash = hash_password(password)
        cursor.execute("""
            SELECT id, username, email FROM users 
            WHERE email = ? AND password_hash = ?
        """, (email, password_hash))
        user = cursor.fetchone()
        conn.close()
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'message': 'Login successful','user': {'id': user['id'],'username': user['username'],'email': user['email']}}), 200
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/user', methods=['GET'])
def get_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, created_at FROM users 
            WHERE id = ?
        """, (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'user': {'id': user['id'],'username': user['username'],'email': user['email'],'created_at': user['created_at']}}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get user', 'details': str(e)}), 500

@app.route('/api/analytics/dashboard', methods=['GET'])
def dashboard_analytics():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    analytics_data = {
        'crowd_density': {
            'current': 75,
            'average': 68,
            'peak': 95
        },
        'traffic_flow': {
            'entrances': 234,
            'exits': 189,
            'net_flow': 45
        },
        'video_analytics': {
            'active_cameras': 8,
            'total_cameras': 10,
            'alerts': 2
        },
        'insights': [
            'Peak crowd density detected at 2:30 PM',
            'Entrance 3 showing highest traffic',
            'Recommended capacity: 85% reached'
        ]
    }
    return jsonify({'analytics': analytics_data}), 200

@app.route('/api/video-analytics', methods=['GET'])
def video_analytics():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    video_data = {
        'cameras': [
            {'id': 1, 'name': 'Entrance 1', 'status': 'active', 'crowd_count': 23},
            {'id': 2, 'name': 'Entrance 2', 'status': 'active', 'crowd_count': 18},
            {'id': 3, 'name': 'Main Hall', 'status': 'active', 'crowd_count': 145},
            {'id': 4, 'name': 'Exit 1', 'status': 'inactive', 'crowd_count': 0}
        ],
        'alerts': [
            {'id': 1, 'message': 'High crowd density in Main Hall', 'severity': 'warning'},
            {'id': 2, 'message': 'Camera 4 offline', 'severity': 'error'}
        ]
    }
    return jsonify({'video_analytics': video_data}), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
