# 🎯 Milestone 4: Administrative Controls, Security & Analytics

This milestone upgrades the project into a **secure, multi-user, and auditable system** with full **Administrative Controls**, **Role-Based Access Control (RBAC)**, and **comprehensive system logging with analytics**.

---

## 🧩 Overview

Milestone 4 focuses on:

- Strengthening **security** using Role-Based Access Control (RBAC)  
- Introducing a dedicated **Admin Dashboard** for system management  
- Enabling **exportable system logs and analytics** for compliance and review  
- Providing **real-time monitoring** of all activities within the platform  

---

## ✅ Features Implemented

### ✔ All Previous Features (Milestones 1–3)
Includes everything implemented in earlier milestones, ensuring complete integration and stability.

---

### 🧑‍💼 Admin Camera & User Management

- Admins can **view, add, edit, and manage** all cameras (both user-linked and global).  
- Access **all user, zone, and camera records** from a unified admin dashboard.  
- Ability to **delete or modify** any user or zone.  
- Fully centralized management from `/admin`.

---

### 📄 Report Downloads

Admins can export all system logs and activity reports in **CSV** or **PDF** format directly from the admin panel.

| Format | Endpoint |
|---------|-----------|
| CSV | `/admin/export-logs/csv` |
| PDF | `/admin/export-logs/pdf` |

---

### 🔐 Role-Based Access Control (RBAC)

- **RBAC enforced at the route level.**
- Only users with `role = 'admin'` can access `/admin/*` endpoints.
- Custom route decorator:

```python
@admin_required
```

ensures only admin users can perform sensitive actions.

All user actions are logged for audit and accountability.

---

## 📊 Complete System Logs & Analytics

- Real-time activity log viewer available at `/admin/activity-log`.
- Visual analytics charts for admin activity, user statistics, and zone performance.
- Exportable historical activity data for compliance and transparency.
- Every log entry records:
  - User  
  - Action  
  - Affected entity  
  - IP address  
  - Timestamp  

---

## ⚙️ Admin API Endpoints

### 👥 Camera & User Management

| Method | Endpoint | Description |
|---------|-----------|-------------|
| GET | `/admin` | Admin dashboard (overview) |
| GET | `/admin/users`, `/admin/zones`, `/admin/cameras` | Tabular view of users, zones, and cameras |
| POST | `/admin/users/delete/<user_id>` | Delete any user (except self) |
| POST | `/admin/cameras/add` | Create and configure new cameras |

---

### 📜 Logs & Analytics

| Method | Endpoint | Description |
|---------|-----------|-------------|
| GET | `/admin/activity-log` | Real-time activity log viewer |
| GET | `/admin/export-logs/csv` | Export all activity logs as CSV |
| GET | `/admin/export-logs/pdf` | Export all activity logs as PDF |

---

### 🔒 Security & RBAC

Every `/admin/*` route validates:

```python
session['role'] == 'admin'
```

Unauthorized users are safely redirected.  
All admin actions are recorded in the `activity_logs` table.  
Users cannot delete their own accounts (safety measure).

---

## 🧭 Usage Guide

### 1️⃣ Log in as an Admin

After registration, a normal user can be promoted to admin via:

- Admin panel controls, or  
- Direct database update (for development).

---

### 2️⃣ Access Admin Panel

Go to `/admin` or click the “Admin Panel” link in the sidebar to:

- View users, cameras, and zones  
- Manage configurations in real time  

---

### 3️⃣ Export Reports

Visit the **Activity Log** section to:

- Download logs as CSV or PDF  
- Filter logs by date or user  

---

### 4️⃣ Review Security & Logs

All critical actions (login, logout, user edits, configuration changes) are logged automatically for auditing and transparency.

---

## 🛡️ Security Considerations

- Full RBAC implemented via route decorators and role checks.  
- Only admins can access `/admin/*` endpoints.  
- Log exports require admin privileges.  
- Self-deletion protection ensures system stability.  

---

## 🧠 Example: Admin Log Export

```python
@app.route('/admin/export-logs/csv')
@admin_required
def export_logs_csv():
    # Exports all logs in CSV format for audit and compliance
    ...
```

---

## 🧩 Database Schema Updates

### 🗂️ activity_logs Table

| Column | Type | Description |
|---------|------|-------------|
| id | INTEGER (PK) | Log ID |
| user_id | INTEGER (FK) | Reference to users table |
| action | TEXT | Description of the action performed |
| entity_type | TEXT | Type of affected entity (user, zone, camera, etc.) |
| entity_id | INTEGER | ID of affected entity |
| details | TEXT | Additional info about the action |
| ip_address | TEXT | IP address of the user |
| timestamp | DATETIME | Action time |

---

### 👤 users Table

| Column | Type | Description |
|---------|------|-------------|
| id | INTEGER (PK) | User ID |
| username | TEXT | Username |
| password | TEXT | Hashed password |
| role | TEXT | user or admin |
| user_jwt | TEXT | Session/login token |

---

## 🏗️ Project Structure (Milestone 4)

```
Milestone_4/
├── app.py                      # Includes RBAC, admin logic, logging, exports
├── templates/
│   ├── admin_dashboard.html    # Admin panel overview
│   ├── admin_users.html        # Manage users
│   ├── admin_zones.html        # Manage zones
│   ├── admin_cameras.html      # Manage cameras
│   ├── admin_activity_log.html # Real-time logs & analytics
│   └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── ...
├── database/
│   └── video_zone.db
└── README.md
```

---

## 📈 Summary

Milestone 4 transforms this project into a **robust, enterprise-ready analytics platform** with:

- Full Administrative Control  
- Secure Role-Based Access Control  
- Comprehensive logging and reporting  
- Data export and compliance tools  

This phase ensures transparency, accountability, and operational safety for multi-user environments.

---

## 🖼️ Screenshots

📸 Add screenshots below for better visual documentation.

- Admin Dashboard Overview  
- User & Camera Management  
- Activity Log Viewer  
- Analytics and Report Exports  

---

## 🧾 License

This project is released under the **MIT License** — free for personal and educational use.

---

## 👨‍💻 Contributors

Developed by **[sasi-upparapalli]**  
📅 Milestone 4 — November 2025
