# Milestone 1: Video Feed and Zone Management with Authentication

## Overview
This milestone implements the foundational features for user authentication and zone management.

## Features Implemented
✅ **JWT-based User Authentication**
- User registration with email validation
- Secure login system with password hashing
- Session management
- User profile management (DOB, Age, Place, Gender)

✅ **Video Feed Acquisition**
- Upload video files (MP4, AVI, MOV)
- Secure file handling with werkzeug
- Video storage in static/uploads directory

✅ **Interactive Zone Management**
- Canvas-based zone drawing tool
- Create, edit, and delete detection zones
- Zone persistence in SQLite database
- Visual zone overlay on video frames

## Project Structure
```
Milestone_1/
├── app.py                      # Flask application with auth & zone routes
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── templates/
│   ├── base.html              # Base template with navigation
│   ├── login.html             # Login page
│   ├── register.html          # Registration page
│   ├── profile.html           # User profile management
│   └── dashboard.html         # Zone management interface
├── static/
│   ├── css/
│   │   └── style.css          # Styling
│   ├── js/
│   │   └── script.js          # Client-side zone drawing logic
│   └── uploads/               # Video upload directory
└── video_zone.db              # SQLite database (auto-created)
```

## Database Schema
### users table
- id (PRIMARY KEY)
- username (UNIQUE)
- email (UNIQUE)
- password (hashed)
- user_jwt (JWT token)

### user_profiles table
- user_id (PRIMARY KEY, FOREIGN KEY)
- dob (Date of Birth)
- age
- place
- gender

### zones table
- id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- video_path
- label (zone name)
- top_left_x, top_left_y
- bottom_right_x, bottom_right_y

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip

### Steps
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   - Open browser to `http://localhost:5000`
   - Register a new account
   - Login and start managing zones

## Usage Guide

### 1. Register an Account
- Navigate to the register page
- Fill in username, email, and password
- Confirm password and submit

### 2. Complete Your Profile
- Go to Profile page
- Add DOB, age, place, and gender
- Save changes

### 3. Upload a Video
- Go to Dashboard
- Click "Upload Video" button
- Select a video file (MP4, AVI, MOV)
- Wait for upload to complete

### 4. Draw Detection Zones
- Click "Start Drawing Zone" button
- Click and drag on the video to draw a rectangle
- Enter a zone label (e.g., "Entrance", "Exit", "Waiting Area")
- Click "Save Zone"
- Repeat for multiple zones

### 5. Manage Zones
- View all saved zones in the zones list
- Edit zone labels by clicking the edit icon
- Delete zones by clicking the delete icon

## API Endpoints

### Authentication
- `POST /register` - Create new user account
- `POST /login` - Authenticate user
- `GET /logout` - End user session
- `GET /profile` - View profile
- `POST /profile` - Update profile

### Zone Management
- `POST /upload-video` - Upload video file
- `POST /save_zone` - Save new zone
- `GET /get_zones` - Retrieve user's zones
- `POST /edit_zone` - Update zone label
- `POST /delete_zone` - Remove zone

## Security Features
- Password hashing with werkzeug
- JWT token generation
- Session-based authentication
- SQL injection prevention with parameterized queries
- Secure file upload with filename sanitization

## Next Steps (Milestone 2)
- Integrate YOLOv8 for person detection
- Implement DeepSORT for tracking
- Add real-time counting within zones

## Notes
- Database is automatically created on first run
- JWT tokens expire after 12 hours
- Upload folder is created automatically if missing
- Maximum file size limits can be configured in Flask

## Troubleshooting
**Issue: Cannot upload video**
- Check file format (must be MP4, AVI, or MOV)
- Ensure static/uploads directory has write permissions

**Issue: Login fails**
- Verify username/password are correct
- Check if user exists in database

**Issue: Zones not saving**
- Ensure video is uploaded first
- Check browser console for JavaScript errors
