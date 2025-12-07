# bb_generation.py

import time
import json
import mss
import numpy as np
from ultralytics import YOLO

class BoundingBoxGenerator:
    def __init__(self, model_path="best.onnx", interval=5):
        self.model = YOLO(model_path)
        self.interval = interval  # seconds
        
        # If your model has classes, list them here (optional)
        # Can also be auto-loaded from model.yaml if available
        try:
            self.class_names = self.model.names
        except:
            self.class_names = {}

    def screenshot(self):
        """Capture full desktop screenshot."""
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Full screen
            img = sct.grab(monitor)
            img_np = np.array(img)[:, :, :3]  # Remove alpha channel (BGRA → BGR)
            return img_np

    def run_detection(self, frame):
        """Run YOLO detection on a frame."""
        results = self.model(frame)
        detections = []

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self.class_names.get(cls_id, str(cls_id))

                detections.append({
                    "bbox": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],  # x, y, w, h
                    "confidence": conf,
                    "class_id": cls_id,
                    "class_name": cls_name
                })

        return detections

    def start(self):
        """Begin continuous detection every X seconds."""
        print("🔥 bb_generation started — capturing desktop every 5 seconds")

        while True:
            frame = self.screenshot()
            detections = self.run_detection(frame)

            output = {
                "timestamp": time.time(),
                "count": len(detections),
                "detections": detections
            }

            print(json.dumps(output, indent=4))
            time.sleep(self.interval)


# Run standalone
if __name__ == "__main__":
    bb = BoundingBoxGenerator("best.onnx", interval=5)
    bb.start()
