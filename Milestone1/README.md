# Crowd Count Analytics Platform

A full-stack web application for crowd analytics and video monitoring with user authentication and real-time dashboard.

## Project Structure

```
project/
├── index.html          # Login & Register Frontend
├── dashboard.html      # Dashboard Frontend  
├── style.css          # Login/Register Page Styling
├── dashboard.css      # Dashboard Page Styling
├── script.js          # Frontend Logic & API Calls
├── app.py             # Backend Flask API
├── requirements.txt   # Python Dependencies
└── README.md          # This file
```

## Features

### Frontend Features
- **Authentication System**: Clean login/register interface with form validation
- **Responsive Dashboard**: Modern sidebar navigation matching the provided design
- **Real-time Analytics**: Dashboard overview with crowd density and traffic flow insights
- **Video Analytics**: Camera monitoring and alert system
- **User Profile**: User account management
- **Session Management**: Persistent login state with logout functionality

### Backend Features
- **RESTful API**: Flask-based backend with comprehensive endpoints
- **User Authentication**: Secure registration and login with password hashing
- **Session Management**: Server-side session handling
- **Database Integration**: SQLite database for user management
- **CORS Support**: Cross-origin resource sharing for frontend-backend communication
- **Analytics Endpoints**: Mock data endpoints for dashboard and video analytics

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Backend Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Flask server:**
   ```bash
   python app.py
   ```

   The backend will be available at `http://localhost:5000`

### Frontend Setup

1. **Serve the frontend files using a web server:**

   **Option 1: Using Python's built-in server:**
   ```bash
   python -m http.server 8000
   ```

   **Option 2: Using Node.js http-server:**
   ```bash
   npx http-server -p 8000
   ```

   **Option 3: Using any web server of your choice**

2. **Access the application:**
   Open your browser and navigate to `http://localhost:8000`

## Usage

### Default Login Credentials
- **Email:** admin@crowdcount.com
- **Password:** password123

### API Endpoints

#### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/user` - Get current user info

#### Analytics
- `GET /api/analytics/dashboard` - Get dashboard analytics
- `GET /api/video-analytics` - Get video analytics data
- `GET /health` - Health check endpoint

### Frontend Pages

#### Login/Register Page (`index.html`)
- Toggle between login and register forms
- Form validation and error handling
- Redirect to dashboard on successful authentication

#### Dashboard (`dashboard.html`)
- Sidebar navigation with multiple sections
- Welcome message with user greeting
- Analytics overview section
- Responsive design matching the provided screenshot

## Development

### Project Architecture
- **Frontend**: Vanilla HTML, CSS, JavaScript with modern ES6+ features
- **Backend**: Python Flask with SQLite database
- **Authentication**: Session-based authentication with password hashing
- **Styling**: Custom CSS with modern design patterns and responsive layout

### Database Schema
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Security Features
- Password hashing using SHA-256
- Session management with secure secret keys
- Input validation and sanitization
- CORS configuration for secure cross-origin requests

## Customization

### Styling
- Modify `style.css` for login/register page styling
- Modify `dashboard.css` for dashboard-specific styling
- Colors and layout can be customized via CSS variables

### Backend Configuration
- Database can be changed from SQLite to PostgreSQL/MySQL by modifying database connection
- Add additional analytics endpoints in `app.py`
- Implement real video analytics integration

### Frontend Features
- Add more dashboard sections and analytics widgets
- Implement real-time data updates using WebSockets
- Add user profile editing functionality

## Production Deployment

### Backend Deployment
1. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. Set up a reverse proxy with Nginx
3. Use a production database (PostgreSQL, MySQL)
4. Configure environment variables for secrets

### Frontend Deployment
1. Deploy static files to a CDN or web server
2. Configure API endpoints for production backend
3. Set up SSL certificates for HTTPS

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For support and questions, please create an issue in the project repository.
