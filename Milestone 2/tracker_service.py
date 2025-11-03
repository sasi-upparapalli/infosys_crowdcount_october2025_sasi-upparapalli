import threading
import time
from typing import Dict, List, Tuple, Optional

import os
import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort


class RealtimeTracker:
    """Encapsulates YOLOv8 + DeepSORT with simple zone counting."""

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
        # self.heatmap: Optional[any] = None # Not used until Milestone 3
        self.zones: List[Dict] = []
        self.current_source: Optional[str | int] = None

    def _lazy_init_models(self) -> None:
        if self.model is None:
            os.environ.setdefault('ULTRALYTICS_FUSE', '0')
            self.model = YOLO("yolov8n.pt")
        if self.tracker is None:
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
            pass

    def start(self, source: str | int, zones: List[Dict], conf: float = 0.4) -> None:
        if self.running and self.current_source == source:
            self.update_zones(zones)
            return
        self.stop()
        self._lazy_init_models()
        self.current_source = source
        self.zones = zones or []
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
        try:
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        self.running = True
        
        # Prime first frame
        try:
            ok, frame0 = self.capture.read()
            if ok:
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

            # height, width = frame.shape[:2] # Not used until Milestone 3
            # self.frame_size = (width, height) # Not used until Milestone 3
            
            try:
                results = self.model(frame, verbose=False, conf=conf, imgsz=416)
            except Exception:
                time.sleep(0.01)
                continue
            
            detections = []
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(float, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                cls_id = int(box.cls[0]) if box.cls is not None else -1
                if cls_id == 0: # Person class
                    detections.append(([x1, y1, w, h], float(box.conf[0]), cls_id))

            try:
                tracks = self.tracker.update_tracks(detections, frame=frame)
            except Exception:
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

                # --- Heatmap logic from Milestone 3 is NOT included here ---

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

            # --- Heatmap overlay logic from Milestone 3 is NOT included here ---

            ok, jpeg = cv2.imencode(".jpg", frame)
            if ok:
                with self.lock:
                    self.latest_frame_jpeg = jpeg.tobytes()
                    self.latest_counts = counts

    def get_latest_frame(self) -> Optional[bytes]:
        with self.lock:
            return self.latest_frame_jpeg

    def get_latest_counts(self) -> Dict[str, int]:
        with self.lock:
            return dict(self.latest_counts)

    def update_zones(self, zones: List[Dict]) -> None:
        with self.lock:
            self.zones = zones or []