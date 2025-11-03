import threading
import time
from typing import Dict, List, Tuple, Optional

import os
import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort


class RealtimeTracker:
    """Encapsulates YOLOv8 + DeepSORT with simple zone counting.

    This service is intentionally minimal and synchronous-friendly, designed
    to plug into Flask streaming endpoints. It maintains its own thread to
    read frames from a source (webcam index or video path) and exposes:
      - latest_frame_jpeg: most recent frame encoded as JPEG bytes
      - latest_counts: dictionary of zone label -> population count
    Zones are axis-aligned rectangles of dict form:
      {label, topLeftX, topLeftY, bottomRightX, bottomRightY}
    """

    def __init__(self) -> None:
        self.model: Optional[YOLO] = None
        self.tracker: Optional[DeepSort] = None
        self.running: bool = False
        self.thread: Optional[threading.Thread] = None
        self.capture: Optional[cv2.VideoCapture] = None
        self.lock = threading.Lock()
        self.latest_frame_jpeg: Optional[bytes] = None
        self.latest_counts: Dict[str, int] = {}
        self.frame_size: Tuple[int, int] = (0, 0)
        self.heatmap: Optional[any] = None
        self.zones: List[Dict] = []
        self.current_source: Optional[str | int] = None

    def _lazy_init_models(self) -> None:
        if self.model is None:
            # Avoid layer fusion issues in some CPU builds
            os.environ.setdefault('ULTRALYTICS_FUSE', '0')
            self.model = YOLO("yolov8n.pt")
        if self.tracker is None:
            # Use built-in MobileNet embedder for stable feature size on CPU
            self.tracker = DeepSort(
                max_age=30,
                embedder="mobilenet",
                embedder_gpu=False,
                half=False,
                bgr=True,
                embedder_model_name="mobilenetv2_x1_4",
            )

    def warmup(self) -> None:
        """Preload models in memory to reduce first-frame latency."""
        try:
            self._lazy_init_models()
        except Exception:
            # Do not crash app on warmup failure; actual start() will retry
            pass

    def start(self, source: str | int, zones: List[Dict], conf: float = 0.4) -> None:
        # If already running on the same source, just update zones and return fast
        if self.running and self.current_source == source:
            self.update_zones(zones)
            return
        self.stop()
        self._lazy_init_models()
        self.current_source = source
        self.zones = zones or []
        # Prefer FFMPEG backend for MP4 stability, fallback to default
        cap = None
        try:
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            ok_test, _ = cap.read()
            if not ok_test:
                cap.release()
                cap = None
        except Exception:
            cap = None
        if cap is None:
            cap = cv2.VideoCapture(source)
        self.capture = cap
        # Reduce latency on some backends
        try:
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        self.running = True
        # Prime first frame so clients see output immediately
        try:
            ok, frame0 = self.capture.read()
            if ok:
                # Quick, low-res prime
                results0 = self.model(frame0, verbose=False, conf=conf, imgsz=416)
                detections0 = []
                for box in results0[0].boxes:
                    x1, y1, x2, y2 = map(float, box.xyxy[0])
                    w, h = x2 - x1, y2 - y1
                    cls_id = int(box.cls[0]) if box.cls is not None else -1
                    if cls_id == 0:
                        detections0.append(([x1, y1, w, h], float(box.conf[0]), cls_id))
                try:
                    tracks0 = self.tracker.update_tracks(detections0, frame=frame0)
                except Exception:
                    tracks0 = []
                # Prepare counts and overlay once
                cz = list(self.zones)
                counts0 = {z["label"]: 0 for z in cz}
                for tr in tracks0:
                    if not tr.is_confirmed():
                        continue
                    x1, y1, x2, y2 = map(int, tr.to_ltrb())
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    for z in cz:
                        if (cx >= int(z["topLeftX"]) and cy >= int(z["topLeftY"]) and
                            cx <= int(z["bottomRightX"]) and cy <= int(z["bottomRightY"])):
                            counts0[z["label"]] += 1
                    cv2.rectangle(frame0, (x1, y1), (x2, y2), (0, 255, 0), 2)
                for z in cz:
                    cv2.rectangle(frame0, (int(z["topLeftX"]), int(z["topLeftY"])),
                                   (int(z["bottomRightX"]), int(z["bottomRightY"])) , (0, 0, 255), 2)
                ok_j, jpeg0 = cv2.imencode(".jpg", frame0)
                if ok_j:
                    with self.lock:
                        self.latest_frame_jpeg = jpeg0.tobytes()
                        self.latest_counts = counts0
        except Exception:
            pass

        self.thread = threading.Thread(target=self._loop, args=(conf,), daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)
        self.thread = None
        if self.capture:
            try:
                self.capture.release()
            except Exception:
                pass
        self.capture = None

    def _loop(self, conf: float) -> None:
        assert self.capture is not None
        while self.running:
            ok, frame = self.capture.read()
            if not ok:
                time.sleep(0.02)
                continue

            height, width = frame.shape[:2]
            self.frame_size = (width, height)
            if self.heatmap is None or self.heatmap.shape[:2] != (height, width):
                self.heatmap = (cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype('float32') * 0)

            try:
                results = self.model(frame, verbose=False, conf=conf, imgsz=416)
            except Exception:
                # If inference fails transiently, skip this frame gracefully
                time.sleep(0.01)
                continue
            detections = []
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(float, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                cls_id = int(box.cls[0]) if box.cls is not None else -1
                # Restrict to person class to keep DeepSORT embeddings stable
                if cls_id == 0:
                    detections.append(([x1, y1, w, h], float(box.conf[0]), cls_id))

            try:
                tracks = self.tracker.update_tracks(detections, frame=frame)
            except Exception:
                # If DeepSORT has a transient failure due to embeddings, skip this frame
                time.sleep(0.01)
                continue

            current_zones = list(self.zones)  # snapshot
            counts: Dict[str, int] = {z["label"]: 0 for z in current_zones}

            for track in tracks:
                if not track.is_confirmed():
                    continue
                x1, y1, x2, y2 = map(int, track.to_ltrb())
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                track_id = getattr(track, 'track_id', None)
                for z in current_zones:
                    if (cx >= int(z["topLeftX"]) and cy >= int(z["topLeftY"]) and
                        cx <= int(z["bottomRightX"]) and cy <= int(z["bottomRightY"])):
                        counts[z["label"]] += 1

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
                if track_id is not None:
                    cv2.putText(frame, f"ID {track_id}", (x1, max(20, y1 - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # Update heatmap using a small gaussian around the center
                if 0 <= cx < width and 0 <= cy < height:
                    size = 25
                    x0, y0 = max(cx - size, 0), max(cy - size, 0)
                    x1h, y1h = min(cx + size, width - 1), min(cy + size, height - 1)
                    patch_w, patch_h = x1h - x0 + 1, y1h - y0 + 1
                    if patch_w > 0 and patch_h > 0:
                        # Build Gaussian kernel that matches (patch_h, patch_w)
                        gx = cv2.getGaussianKernel(patch_w, 8)
                        gy = cv2.getGaussianKernel(patch_h, 8)
                        heat_patch = gy @ gx.T  # shape (patch_h, patch_w)
                        self.heatmap[y0:y1h+1, x0:x1h+1] += heat_patch

            for z in current_zones:
                cv2.rectangle(
                    frame,
                    (int(z["topLeftX"]), int(z["topLeftY"])),
                    (int(z["bottomRightX"]), int(z["bottomRightY"])) ,
                    (0, 0, 255), 2,
                )
                label = f"{z['label']}: {counts[z['label']]}"
                cv2.putText(frame, label, (int(z["topLeftX"]) + 5, int(z["topLeftY"]) - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Apply decay to heatmap and overlay
            if self.heatmap is not None:
                self.heatmap *= 0.95  # decay
                hm_norm = cv2.normalize(self.heatmap, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')
                hm_color = cv2.applyColorMap(hm_norm, cv2.COLORMAP_JET)
                overlay = cv2.addWeighted(frame, 0.75, hm_color, 0.25, 0)
                frame = overlay

            ok, jpeg = cv2.imencode(".jpg", frame)
            if ok:
                with self.lock:
                    self.latest_frame_jpeg = jpeg.tobytes()
                    self.latest_counts = counts

        # loop end

    def get_latest_frame(self) -> Optional[bytes]:
        with self.lock:
            return self.latest_frame_jpeg

    def get_latest_counts(self) -> Dict[str, int]:
        with self.lock:
            return dict(self.latest_counts)

    def update_zones(self, zones: List[Dict]) -> None:
        # Replace zones atomically; loop will pick up snapshot next frame
        with self.lock:
            self.zones = zones or []


