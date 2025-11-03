# Milestone 3: Live Dashboard and Alert System

## Overview
This milestone adds real-time streaming capabilities, data visualization, and threshold-based alerts.

## Features Implemented
✅ **All Previous Features** (Milestones 1 & 2)

✅ **Real-Time Dashboard with WebSockets**
- Live video streaming with MJPEG
- Server-Sent Events (SSE) for real-time stats
- Separate live dashboard page (`/live`)
- Auto-updating zone counts

✅ **Data Visualization**
- Real-time count displays per zone
- Heatmap overlay on video feed
- Visual threshold indicators
- Color-coded alerts (green/red)

✅ **Alert System**
- Configurable thresholds per zone
- Visual in-app alerts when counts exceed limits
- Threshold persistence in database
- Real-time threshold checking

## New Project Structure
```
Milestone_3/
├── app.py                      # Full version with streaming
├── tracker_service.py          # Complete with heatmaps
├── templates/
│   ├── live.html              # NEW: Live dashboard
│   └── [All previous templates]
├── [All files from Milestone 2]
```

## New Features in Detail

### 1. Live Streaming Routes
```python
# Video feed streaming
@app.route('/video_feed')
def video_feed():
    # Returns MJPEG stream

# Real-time statistics
@app.route('/stats_stream')
def stats_stream():
    # Server-Sent Events for counts & thresholds
```

### 2. Threshold Management
```python
# Set thresholds for zones
@app.route('/set_thresholds', methods=['POST'])

# Get saved thresholds
@app.route('/get_thresholds', methods=['GET'])
```

### 3. Enhanced Tracker Service
- **Heatmap Generation**: Gaussian accumulation at person locations
- **Heatmap Overlay**: Blended with video frame (25% opacity)
- **Decay System**: Heatmap fades over time (95% retention per frame)

## Installation & Setup

### Prerequisites
Same as Milestone 2, plus:
- Modern web browser with EventSource support
- Stable network connection for streaming

### Steps
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access dashboards:**
   - Zone Management: `http://localhost:5000/dashboard`
   - Live Monitoring: `http://localhost:5000/live`

## Usage Guide

### 1. Set Up Zones (Dashboard)
- Upload video
- Draw and save zones
- Configure zone names

### 2. Configure Thresholds (Live Dashboard)
- Navigate to `/live`
- Enter threshold values for each zone
- Click "Set Thresholds" to save

### 3. Start Live Monitoring
- Click "Start Stream" button
- Select source:
  - **Uploaded Video**: Processes your uploaded file
  - **Webcam**: Uses device camera (if available)
- Monitor real-time counts and alerts

### 4. Interpret Visualizations
- **Heatmap colors**:
  - Blue: Low activity
  - Green/Yellow: Moderate activity
  - Red: High activity (hotspots)
- **Alert indicators**:
  - Green count: Below threshold
  - Red count: Exceeds threshold ⚠️

## API Endpoints

### Streaming
- `POST /start_stream` - Begin real-time processing
- `POST /stop_stream` - Stop streaming
- `GET /video_feed` - MJPEG video stream
- `GET /stats_stream` - SSE for counts/thresholds

### Thresholds
- `POST /set_thresholds` - Save zone thresholds
  ```json
  {
    "Entrance": 10,
    "Exit": 5,
    "Waiting Area": 20
  }
  ```
- `GET /get_thresholds` - Retrieve saved thresholds

## Technical Implementation

### Server-Sent Events (SSE)
```javascript
const evtSource = new EventSource('/stats_stream');
evtSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    updateCounts(data.counts);
    checkThresholds(data.thresholds);
};
```

### MJPEG Streaming
```python
def gen():
    while True:
        frame = get_tracker().get_latest_frame()
        if frame:
            yield (b'--frame
'
                   b'Content-Type: image/jpeg

' 
                   + frame + b'
')
```

### Heatmap Algorithm
```python
# Gaussian kernel accumulation
gx = cv2.getGaussianKernel(patch_w, 8)
gy = cv2.getGaussianKernel(patch_h, 8)
heat_patch = gy @ gx.T
heatmap[y0:y1, x0:x1] += heat_patch

# Decay over time
heatmap *= 0.95

# Normalize and colorize
hm_norm = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX)
hm_color = cv2.applyColorMap(hm_norm, cv2.COLORMAP_JET)

# Blend with video
overlay = cv2.addWeighted(frame, 0.75, hm_color, 0.25, 0)
```

## Database Schema Updates

### zone_thresholds table (NEW)
- user_id (FOREIGN KEY)
- zone_label
- threshold (INTEGER)
- PRIMARY KEY (user_id, zone_label)

## Configuration Options

### Adjust Stream Update Rate
In `stats_stream()`:
```python
time.sleep(0.5)  # Update every 500ms
```

### Change Heatmap Opacity
In `tracker_service.py`:
```python
overlay = cv2.addWeighted(frame, 0.75, hm_color, 0.25, 0)
#                                 ^^^^           ^^^^
#                                 video         heatmap
```

### Modify Alert Colors
In `static/js/script.js`:
```javascript
if (count > threshold) {
    countElement.style.color = 'red';    // Alert color
} else {
    countElement.style.color = 'green';  // Normal color
}
```

## Advanced Features

### Dynamic Zone Updates
Zones can be modified without restarting the stream:
```python
@app.route('/edit_zone', methods=['POST'])
def edit_zone():
    # Update database
    # Refresh tracker zones immediately
    updated_zones = _load_user_zones()
    get_tracker().update_zones(updated_zones)
```

### Multi-Source Support
The system automatically handles:
- Uploaded video files
- Webcam (source=0)
- IP camera streams (RTSP URLs)

## Performance Tips

### For Smooth Streaming
1. **Reduce frame size**: Lower resolution = higher FPS
2. **Adjust JPEG quality**: Trade quality for speed
3. **Limit simultaneous viewers**: Each stream = 1 thread
4. **Use GPU**: 3-4x faster than CPU

### For Accurate Heatmaps
1. **Longer decay time**: Increase `heatmap *= 0.98`
2. **Larger Gaussian kernel**: Wider blur radius
3. **Higher accumulation**: Multiply heat_patch by factor

## Troubleshooting

**Issue: Video feed not loading**
- Check browser console for errors
- Verify stream started (`/start_stream` called)
- Ensure firewall allows local connections

**Issue: Stats not updating**
- Check EventSource connection in Network tab
- Verify `/stats_stream` endpoint is accessible
- Browser may limit SSE connections (max ~6)

**Issue: High CPU usage**
- Reduce inference resolution (`imgsz=320`)
- Lower frame rate (add delay in loop)
- Stop stream when not in use

**Issue: Alerts not triggering**
- Verify thresholds are saved (check `/get_thresholds`)
- Ensure counts are being calculated
- Check browser console for JavaScript errors

## Known Limitations
- **No email alerts yet**: Currently only in-app visual alerts
- **Single stream per user**: Multiple tabs may conflict
- **No historical data**: Stats reset on stream restart
- **Browser compatibility**: Requires EventSource support

## Future Enhancements (Milestone 4)
- Email/SMS alerts via SMTP/Twilio
- Historical data logging and charts (Chart.js)
- Activity logs and audit trail
- Admin panel with RBAC
- Multi-user concurrent streaming

## Testing Scenarios

### Scenario 1: Basic Monitoring
1. Start stream
2. Set threshold to 5 for "Entrance"
3. Wait for detection
4. Verify alert when count > 5

### Scenario 2: Multiple Zones
1. Create 3 zones with different thresholds
2. Start stream
3. Observe independent counting
4. Check heatmap highlights busy areas

### Scenario 3: Dynamic Updates
1. Start stream
2. Edit zone label
3. Verify count persists with new label
4. Delete zone
5. Confirm removal from live view

## Performance Benchmarks
- **Streaming latency**: ~200-500ms (local)
- **SSE update interval**: 500ms (configurable)
- **Memory usage**: ~800MB-1.5GB (with heatmap)
- **Network bandwidth**: ~2-5 Mbps (depends on resolution)

## Security Considerations
- Session-based stream access control
- User-isolated zone/threshold data
- No cross-user data leakage
- Secure video file paths (no directory traversal)

## References
- [Server-Sent Events Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [MJPEG Streaming](https://en.wikipedia.org/wiki/Motion_JPEG)
- [OpenCV Heatmap Tutorial](https://docs.opencv.org/4.x/d3/d50/group__imgproc__colormap.html)
