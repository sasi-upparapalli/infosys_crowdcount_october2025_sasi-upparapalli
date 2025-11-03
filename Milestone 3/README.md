# Crowd Count using Video Analytics

## Overview

This project is a smart video analytics system designed to monitor and manage crowd levels in real time. It combines computer vision, deep learning, and secure user management to deliver a full-stack solution for intelligent crowd monitoring.

With this system, users can:

  * Log in securely with authentication and session management.
  * Manage a personal user profile with additional details.
  * Upload video streams and define custom monitoring zones.
  * Track and count people in each zone using AI-based detection and tracking.
  * Visualize live crowd data through charts, heatmaps, and video overlays.
  * Receive alerts when a crowd exceeds safe thresholds.

The solution is applicable to **malls, events, stadiums, transport hubs, or public safety environments** where crowd control is critical.


## Features

#### Secure User Management & Profiles

  * **Secure Authentication:** Robust registration and login system for user access.
  * **User Profile Page:** A dedicated page for users to view their account details (username, email) and manage additional personal information like date of birth, age, place, and gender.
  * **Password Security:** Passwords are never stored in plain text and are securely hashed.
  * **Session Management:** JWT-based authentication ensures secure and scalable user sessions.

#### Zone Management

  * **Interactive Zone Creation:** Upload videos and **draw, edit, save, and manage zones** directly on the video frame.
  * **Persistent Storage:** Zone data and custom thresholds are saved in a database for each user.

#### Real-Time Analytics

  * **Live Dashboard:** A comprehensive dashboard with zone-wise crowd counts, updated in real time.
  * **Unique ID Tracking:** Utilizes **YOLO + DeepSORT** to assign persistent IDs to individuals, preventing double counting as they move.
  * **Data Visualization:** Includes line charts for population trends and heatmap overlays to highlight crowd density on the video feed.
  * **Smart Alerts:** The system automatically triggers alerts when the number of people in a zone exceeds the user-defined threshold.


## Project Workflow

1.  **User Onboarding** – New users create an account through a simple registration page. Existing users can log in securely through the login page.
2.  **Profile Management** – After logging in, users can visit their profile page to view account details and add personal information.
3.  **Video & Zone Setup** – Users can upload a video or use a webcam feed, then draw custom zones to define monitoring areas.
4.  **Real-Time Monitoring** – The system tracks individuals with unique IDs, counts them within each zone, and displays the data on a live dashboard.
5.  **Visualization & Alerts** – Users can monitor trends with charts and heatmaps and receive notifications when a zone's capacity is exceeded.


## Getting Started

#### Prerequisites

  * Python 3.9+
  * pip (Python package manager)
  * Git

#### Installation

1.  **Clone the repository**

    git clone https://github.com/tejaswinirayavarapu/Crowd-Count-using-Video-Analytics.git
    
    cd Crowd-Count-using-Video-Analytics

3.  **Create and activate a virtual environment**
    python -m venv venv
    
    *On Windows:*
    venv\Scripts\activate
    
    *On Mac/Linux:*
    source venv/bin/activate
4.  **Install dependencies**
    pip install -r requirements.txt
5.  **Run the application**
    python app.py
6.  **Access the app**
    Open `http://127.0.0.1:5000` in your browser.


## Application Walkthrough

1.  **Login and Registration**
    The application starts with a **Login Page**. New users can navigate to the **Registration Page** to create a secure account by providing a username, email, and password.

2.  **User Profile**
    After logging in, users can click the **"User Information"** button in the sidebar. This leads to a profile page where they can view their registration details and add or update personal information like date of birth, age, and gender.
    <img width="1877" height="887" alt="Screenshot 2025-10-05 213427" src="https://github.com/user-attachments/assets/3184e9d2-b09d-4a1c-8af7-993e2cc4f503" />
    
3.  **Zone Manipulation Dashboard**
    The main dashboard features a "Zone Manipulation" menu with several options:

      * **Upload Video or Use Webcam:** The user can start by providing a video source.
      <img width="1886" height="881" alt="Screenshot 2025-10-05 213501" src="https://github.com/user-attachments/assets/5729acdc-fb41-4621-bd61-686006e85a93" />
      <img width="1863" height="885" alt="Screenshot 2025-10-05 213602" src="https://github.com/user-attachments/assets/aae16344-b9fc-4958-9849-daf11bf76ab6" />

      * **Draw Zones:** After a video is loaded, the user can draw rectangular zones over the video to define areas for monitoring.
      <img width="1899" height="875" alt="Screenshot 2025-10-05 213649" src="https://github.com/user-attachments/assets/f3c8735e-25e8-4695-83c8-c849b2bc26ca" />

      * **Preview & Track IDs:** Users can preview the zones they've drawn or click "Track ID" to see the live tracking with unique IDs assigned to each person.
        <img width="1876" height="877" alt="Screenshot 2025-10-05 213816" src="https://github.com/user-attachments/assets/bc0a1116-6736-429d-aaa6-843fd2dc906e" />
        <img width="1798" height="882" alt="Screenshot 2025-10-05 213859" src="https://github.com/user-attachments/assets/093036d2-8fa3-4312-aa41-393fac559686" />

      * **Edit & Delete Zones:** Existing zones can be renamed or deleted as needed.
        <img width="1892" height="827" alt="Screenshot 2025-10-05 213929" src="https://github.com/user-attachments/assets/d6c15b63-ccb5-4fdd-b760-7f67e41744b8" />
        <img width="1872" height="830" alt="Screenshot 2025-10-05 214012" src="https://github.com/user-attachments/assets/b3afbead-8afa-4ea7-a3ca-4a5ad27bbe85" />

4.  **Live Dashboard**
    When the user clicks on the "Live Dashboard," they can view:

      * Real-time population counts for each zone.
      * Line chart visualizations showing population trends over time.
      * Heatmap overlays on the live video feed to highlight crowded areas.
      * An alert system that notifies the user when any zone exceeds its set capacity.
<img width="1478" height="895" alt="Screenshot 2025-10-05 214125" src="https://github.com/user-attachments/assets/e33fe2be-d80b-444a-95d1-30cf8e8cc104" />


## Tech Stack

  * **Languages:** Python, JavaScript
  * **Frameworks:** Flask
  * **Computer Vision:** OpenCV, YOLO, DeepSORT
  * **Database:** SQLite
  * **Security:** Password Hashing, JWT
