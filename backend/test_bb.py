# test_bb_generation.py

from bb_generation import BoundingBoxGenerator
import json
import time

def pretty_print(data):
    """Pretty-print bounding boxes with indentation."""
    print(json.dumps(data, indent=4))

def main():
    # Initialize the bounding box generator
    bb_gen = BoundingBoxGenerator(model_path="best.onnx", interval=5)
    
    print("Starting bounding box testing (press Ctrl+C to stop)...")
    
    try:
        while True:
            # Capture screenshot and run YOLO detection
            frame = bb_gen.screenshot()
            detections = bb_gen.run_detection(frame)
            
            output = {
                "timestamp": time.time(),          # UNIX timestamp
                "device": "ONNX Runtime CPU",      # fixed string
                "count": len(detections),
                "detections": detections
            }
            
            # Print results nicely
            pretty_print(output)
            
            # Wait for the interval before the next capture
            time.sleep(bb_gen.interval)
            
    except KeyboardInterrupt:
        print("\nTest stopped by user.")

if __name__ == "__main__":
    main()
