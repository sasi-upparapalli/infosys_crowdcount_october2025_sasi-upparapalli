# 🎓 CrowdCount: People Counting Using Video Analytics
### Infosys Certified Final Project – 2025  
**Tagline:** *A Smart Vision-Based System for Real-Time Crowd Monitoring*

---

## 🧠 Overview

**CrowdCount** is a real-time **AI-powered crowd analytics system** designed to detect, track, and count people across multiple surveillance zones using **computer vision**.  
It enables administrators and security operators to monitor crowd density, set zone thresholds, and get instant alerts when thresholds are exceeded — all through an elegant **Flask-based web dashboard**.

---

## 🚀 Key Features

- 🎥 **Live Camera Streaming** — Stream from webcam or connected IP cameras in real time.  
- 🧩 **Smart Zone Drawing** — Define custom regions of interest (ROI) directly on the live or uploaded video feed.  
- 🧍 **Accurate People Tracking** — Uses **YOLOv8** + **Deep SORT**-based tracking with over **90% accuracy**.  
- 🧮 **Zone-Based Counting** — Dynamically counts unique individuals per defined zone.  
- 📊 **Interactive Dashboard** — Displays real-time stats, live heatmaps, and alerts.  
- 🛡️ **Role-Based Access** — Secure admin and user panels with Flask session management.  
- 🗂️ **Export & Reports** — Export system logs, activity data, and camera reports in **CSV/PDF** format.  
- 🔔 **Alerts & Thresholds** — Instant notifications when zone capacity limits are exceeded.  
- 🧾 **Comprehensive Logs** — Tracks every admin/user action for audit and compliance.

---

## 🧩 Tech Stack

| Layer | Technology |
|--------|-------------|
| **Frontend** | HTML5, CSS3 (Custom Theme), JavaScript (Canvas + Chart.js) |
| **Backend** | Flask (Python 3.x) |
| **Database** | SQLite3 |
| **ML/AI Engine** | YOLOv8 (Ultralytics) + Deep SORT for tracking |
| **Visualization** | Chart.js (live line & bubble charts) |
| **Authentication** | JWT-based sessions, Flask-login |
| **Exports** | CSV, FPDF |
| **Deployment** | Render / Local Flask Server |
| **File Structure** | `/static`, `/templates`, `/uploads`, `/admin`, `/models` |

---

## 📂 Project Structure

```
CrowdCount_Project/
│
├── app.py # Flask main backend
├── tracker_service.py # Tracking and detection logic (YOLOv8)
├── video_zone.db # SQLite3 database
│
├── static/
│ ├── css/style.css # Frontend theme and layout
│ ├── js/script.js # Core frontend logic (zones, webcam, uploads)
│ └── uploads/ # Uploaded media files
│
├── templates/
│ ├── dashboard.html # User dashboard
│ ├── live.html # Live analytics dashboard
│ ├── admin_dashboard.html # Admin dashboard overview
│ ├── admin_users.html # Manage users
│ ├── admin_zones.html # Manage zones
│ ├── admin_cameras.html # Manage cameras
│ ├── admin_activity_log.html # Activity logs & reports
│ └── base.html
│
└── requirements.txt
```

---

## 🧭 Milestone-Based Progress Evaluation

### 🥇 **Milestone 1 (Week 2) — Initial Setup**
**Goals:**
- Stream camera successfully.  
- Save and render zones on live feed.  
- Interface for zone editing functional.  

**Implemented:**
- Webcam and upload functionality (`script.js → startWebcam()` / `/upload-video`).  
- Zone drawing via canvas with dynamic storage.  
- Edit/Delete zones through API routes `/save_zone`, `/edit_zone`, `/delete_zone`.  


---

### 🥈 **Milestone 2 (Week 4) — Detection & Tracking**
**Goals:**
- Detection and tracking with >90% accuracy.  
- Unique people ID tracking across frames.  
- Real-time zone-based counting updates.  

**Implemented:**
- YOLOv8 + Deep SORT tracking integrated in `tracker_service.py`.  
- `/zm_start_tracking` endpoint triggers live tracking overlay.  
- Real-time tracking frame feed streamed via `/zm_feed`.  


---

### 🥉 **Milestone 3 (Week 6) — Visualization and Alerts**
**Goals:**
- Dashboard shows updated stats and live heatmap.  
- Export features and alerts functional.  
- Visuals are responsive and easy to interpret.  

**Implemented:**
- `live.html` dashboard with **Chart.js** line & bubble charts.  
- Real-time updates via **Server-Sent Events (SSE)** `/stats_stream`.  
- Zone-based thresholds adjustable from dashboard.  
- Alerts triggered on threshold breaches.  
- Export buttons for CSV and PDF (`/export_logs_csv`, `/export_logs_pdf`).  


---

### 🏅 **Milestone 4 (Week 8) — Administration & Security**
**Goals:**
- Admin controls all camera settings and downloads reports.  
- Secure role-based access working correctly.  
- System logs and analytics complete.  

**Implemented:**
- Admin panel with dedicated views for users, cameras, zones, and logs.  
- Role-based authentication (Admin/User).  
- Full audit logging system (`admin_activity_log.html`).  
- Data export, pagination, and filtering.  

---

## ⚙️ Setup and Installation

### Prerequisites
- Python 3.9 or higher  
- pip package manager  
- Virtual environment (recommended)

### Installation Steps
```bash
git clone https://github.com/yourusername/CrowdCount.git
cd CrowdCount_Project
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
python app.py
```
Visit 👉 http://127.0.0.1:5000

---

## 🧠 Future Enhancements

- 🤖 **Deep Learning on Edge Devices** – Optimize YOLO for Jetson Nano / Raspberry Pi.
- 🕵️ **Anomaly Detection** – Identify unusual crowd movements or density patterns.
- 📱 **Mobile View** – Progressive Web App (PWA) for remote monitoring.
- ☁️ **Cloud Integration** – Push analytics to AWS or Azure dashboards.
- 🔉 **Audio Alerts** – Real-time audio/voice alerts for crowd overflow.
- 📡 **Multi-Camera Synchronization** – Merge analytics across multiple feeds.

---

## 🧾 Credits

Developed by **Upparapalli Surya Sasikanth**  
Under **Infosys Certified Final Project – 2025**  
Supervised by the Infosys Training & Evaluation Team.

---

## 🖼️ Screenshots Section

| Feature | Screenshot |
|----------|-------------|
| Login & Register Page|[![Login-Page.png](https://i.postimg.cc/W1tffK9g/Login-Page.png)](https://postimg.cc/JsVqsTCz)|
| Zone Drawing | [![Zone-Drawing-Tool.png](https://i.postimg.cc/qMdSmjnp/Zone-Drawing-Tool.png)](https://postimg.cc/F1DTzbD6) |
| Tracking Feed |[![Track-Id-s.png](https://i.postimg.cc/YS3C9vHG/Track-Id-s.png)](https://postimg.cc/NyKcCfLB)|
| Live Dashboard |[![Alerts-by-Threshold.png](https://i.postimg.cc/gJJBZTfZ/Alerts-by-Threshold.png)](https://postimg.cc/B8rgWMZS) |
| Admin Panel | [![Admin-Dashboard.png](https://i.postimg.cc/B6RThYV0/Admin-Dashboard.png)](https://postimg.cc/phY5rZvG)|
| Reports Export |[![Active-Log-Data-To-export.png](https://i.postimg.cc/3xwPQWw4/Active-Log-Data-To-export.png)](https://postimg.cc/kBkjxJKq)|

---

## 🧩 License
This project is licensed under the **MIT License** — free to use, modify, and distribute.

> “CrowdCount — because every person counts, and every crowd matters.” 💡
