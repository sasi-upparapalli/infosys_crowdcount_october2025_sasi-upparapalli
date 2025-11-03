# Milestone 2: People Detection and Counting

## Overview
This milestone builds upon Milestone 1 by integrating YOLOv8 for person detection and DeepSORT for multi-object tracking.

## Features Implemented
✅ **All Milestone 1 Features** (Authentication, Video Upload, Zone Management)

✅ **YOLOv8 Person Detection**
- Real-time person detection using YOLOv8n model
- Optimized inference with confidence threshold (default: 0.4)
- Bounding box visualization on video frames

✅ **DeepSORT Multi-Object Tracking**
- Persistent ID assignment for tracked persons
- MobileNet embedder for feature extraction
- Track management with age-based filtering

✅ **Zone-Based Counting**
- Count persons within each defined zone
- Center-point zone membership detection
- Real-time count updates
- Heatmap generation for movement patterns

## New Project Structure
```
Milestone_2/
├── app.py                      # Enhanced with tracking routes
├── tracker_service.py          # NEW: YOLOv8 + DeepSORT service
├── requirements.txt            # Updated dependencies
├── README.md                   # This file
├── yolov8n.pt                  # YOLOv8 nano model weights
├── [All files from Milestone 1]
```

## New Dependencies
- `ultralytics` - YOLOv8 implementation
- `deep-sort-realtime` - DeepSORT tracker
- `opencv-python` - Video processing
- `torch` - PyTorch for model inference

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- (Optional) CUDA-enabled GPU for faster inference

### Steps
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Download YOLOv8 model (if not included):**
   ```python
   from ultralytics import YOLO
   model = YOLO("yolov8n.pt")  # Auto-downloads on first run
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

## New API Endpoints

### Zone Manipulation Tracking
- `POST /zm_start_tracking` - Start tracking preview with DeepSORT IDs
- `POST /zm_stop_tracking` - Stop tracking preview
- `GET /zm_feed` - MJPEG stream with tracking visualization

## Usage Guide

### 1. Complete Milestone 1 Setup
- Register account
- Upload video
- Draw zones

### 2. Preview Tracking on Uploaded Video
- Go to Dashboard
- Your uploaded video will show in the preview area
- Click "Start Tracking Preview"
- See persons detected with bounding boxes
- Track IDs appear above each person
- Zone counts display on each zone rectangle

### 3. View Tracking Results
- **Green boxes**: Detected and tracked persons
- **Red boxes**: Defined zones
- **Green dots**: Person center points
- **ID labels**: Persistent tracker IDs
- **Zone labels**: Show real-time counts (e.g., "Entrance: 5")

## Technical Details

### tracker_service.py Architecture
```python
class RealtimeTracker:
    - model: YOLO          # YOLOv8n for detection
    - tracker: DeepSort    # For persistent IDs
    - zones: List[Dict]    # Detection zones
    - heatmap: np.array    # Accumulates movement
```

### Detection Pipeline
1. **Frame Capture**: Read from video file or webcam
2. **Detection**: YOLOv8 detects persons (class ID 0)
3. **Tracking**: DeepSORT assigns persistent IDs
4. **Zone Counting**: Check if person center is inside zones
5. **Visualization**: Draw boxes, IDs, zones, counts
6. **Heatmap Update**: Accumulate Gaussian at person locations
7. **Frame Encoding**: JPEG compression for streaming

### Performance Optimizations
- **Model preloading**: Loads on app startup to reduce first-frame latency
- **Low-res inference**: Uses 416x416 imgsz for faster processing
- **Buffer reduction**: Single-frame buffer to minimize lag
- **Threaded processing**: Background thread for video loop
- **Frame skipping**: Graceful handling of slow inference

### Zone Counting Logic
```python
# Person is in zone if center point is inside rectangle
cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
if (cx >= zone.topLeftX and cy >= zone.topLeftY and
    cx <= zone.bottomRightX and cy <= zone.bottomRightY):
    counts[zone.label] += 1
```

## Configuration

### Adjust Detection Confidence
In `tracker_service.py`, modify the `conf` parameter:
```python
results = self.model(frame, verbose=False, conf=0.4)  # 0.0 to 1.0
```

### Change Model Size
Replace `yolov8n.pt` with larger models for better accuracy:
- `yolov8s.pt` - Small (faster, less accurate)
- `yolov8m.pt` - Medium
- `yolov8l.pt` - Large (slower, more accurate)

### Heatmap Decay Rate
In `_loop()` method:
```python
self.heatmap *= 0.95  # Lower = faster fade, Higher = longer memory
```

## Troubleshooting

**Issue: Model not loading**
- Ensure `yolov8n.pt` is in the root directory
- Check PyTorch installation: `pip install torch torchvision`

**Issue: Slow tracking**
- Reduce video resolution
- Use smaller YOLO model (yolov8n is smallest)
- Disable heatmap generation temporarily

**Issue: Inaccurate IDs**
- DeepSORT may reassign IDs if person leaves frame
- Adjust `max_age` parameter in DeepSORT initialization

**Issue: Memory error**
- Reduce frame buffer size
- Close other applications
- Use CPU instead of GPU if GPU memory is full

## Known Limitations
- Only detects persons (class 0), not other objects
- Track IDs may be reassigned if person re-enters frame
- Performance depends on hardware (CPU vs GPU)
- Heatmap accumulates indefinitely (no auto-reset)

## Next Steps (Milestone 3)
- Real-time dashboard with WebSocket streaming
- Chart.js visualizations for occupancy trends
- Email/in-app alerts when zone thresholds exceeded

## Performance Benchmarks
- **YOLOv8n + CPU**: ~10-15 FPS (640x480 video)
- **YOLOv8n + GPU**: ~30-60 FPS (640x480 video)
- **Memory usage**: ~500MB-1GB (depends on model)

## References
- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [DeepSORT Paper](https://arxiv.org/abs/1703.07402)
- [Deep SORT Realtime](https://github.com/levan92/deep_sort_realtime)
