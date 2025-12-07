# main.py
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow logs

import warnings
warnings.filterwarnings("ignore")

import random
import json
import threading
import time
from fastapi import FastAPI, UploadFile, File, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from stt import transcribe_wav
from intent_engine import classify_intent
from fusion import fusion
from analyzer import ScreenAnalyzer
from bb_generation import BoundingBoxGenerator
from tts import get_tts_instance

import uvicorn
# --------------------------------------------------------------------
# FastAPI app
# --------------------------------------------------------------------
app = FastAPI(title="AI Companion Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------
# Initialize YOLO BoundingBoxGenerator
# --------------------------------------------------------------------
bb_generator = BoundingBoxGenerator(model_path="best.onnx", interval=5)
bb_generator.latest_result = None  # store latest detections

# Add a lock to guard latest_result access
bb_lock = threading.Lock()

def bb_loop():
    """Background loop to continuously update latest_result."""
    print("🔥 YOLO bounding box generator started in background")
    while True:
        try:
            frame = bb_generator.screenshot()
            detections = bb_generator.run_detection(frame)
            res = {
                "timestamp": time.time(),
                "count": len(detections),
                "detections": detections
            }
            with bb_lock:
                bb_generator.latest_result = res
        except Exception as e:
            print(f"BB loop error: {e}")
        time.sleep(bb_generator.interval)

# Start YOLO in a separate thread to avoid blocking FastAPI
threading.Thread(target=bb_loop, daemon=True).start()

# --------------------------------------------------------------------
# Initialize Screen Analyzer
# --------------------------------------------------------------------
screen_analyzer = ScreenAnalyzer(
    ocr_engine="easyocr",
    use_gpu=False
)

# --------------------------------------------------------------------
# WebSocket connections
# --------------------------------------------------------------------
connections = set()

async def broadcast(message: dict):
    """Send Unity-safe JSON to all connections."""
    def sanitize(obj):
        if isinstance(obj, dict):
            sanitized = {}
            for k, v in obj.items():
                if isinstance(v, (int, float, str, bool, list, type(None))):
                    sanitized[k] = v
                elif isinstance(v, dict):
                    sanitized[k] = sanitize(v)
                else:
                    sanitized[k] = str(v)
            return sanitized
        elif isinstance(obj, list):
            return [sanitize(i) for i in obj]
        else:
            return str(obj)

    safe_message = sanitize(message)
    data = json.dumps(safe_message)
    for ws in list(connections):
        try:
            await ws.send_text(data)
        except Exception:
            try:
                connections.remove(ws)
            except:
                pass

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    print("✅ WebSocket connected")
    try:
        while True:
            # If Unity sends messages, we optionally handle simple pings
            try:
                msg_text = await ws.receive_text()
                if not msg_text:
                    continue
                # attempt to parse incoming JSON and respond to pings
                try:
                    obj = json.loads(msg_text)
                    if isinstance(obj, dict) and obj.get("type") == "ping":
                        await ws.send_text(json.dumps({"type": "pong"}))
                except Exception:
                    # ignore non-json or unexpected messages
                    pass
            except Exception:
                break
    finally:
        try:
            connections.remove(ws)
        except:
            pass
        print("🔌 WebSocket disconnected")

# --------------------------------------------------------------------
# Helper: Broadcast NLP + Action messages (3A)
# --------------------------------------------------------------------
async def broadcast_nlp_and_action(uid: int, text: str, nlp: dict, action: dict):
    """
    Broadcasts two messages:
      - nlp_result: contains intent/slots/reply for Unity to speak or display
      - action_result: contains action, slots, status for execution tracking
    """
    # Build nlp_result payload
    nlp_payload = {
        "type": "nlp_result",
        "id": uid,
        "text": text,
        "intent": nlp.get("intent", "none"),
        "slots": nlp.get("slots", {}),
        "reply": nlp.get("reply", "")
    }

    # Build action_result payload
    action_payload = {
        "type": "action_result",
        "id": uid,
        "action": action.get("action", "none"),
        "slots": action.get("slots", {}),
        "reply": action.get("reply", ""),
        "status": action.get("status", "ok")
    }

    # Broadcast both (NLP first so Unity can speak before action if desired)
    await broadcast(nlp_payload)
    await broadcast(action_payload)

    # Return combined dict for HTTP response if needed
    return {"nlp": nlp_payload, "action": action_payload}

# --------------------------------------------------------------------
# NLP Voice Intent
# --------------------------------------------------------------------
@app.post("/stt")
async def nlp_from_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    uid = random.randint(10000, 99999)

    # 1. Transcribe audio
    try:
        text = transcribe_wav(audio_bytes)
    except Exception as e:
        text = ""
        print(f"STT error: {e}")

    # 2. Classify intent and fuse with CV/action system
    nlp = classify_intent(text or "")
    action = fusion.fuse(nlp)

    # 3. Broadcast both nlp_result and action_result
    result = await broadcast_nlp_and_action(uid, text, nlp, action)

    # 4. Return combined response
    return {
        "status": "ok",
        "id": uid,
        "text": text,
        "nlp": result["nlp"],
        "action": result["action"]
    }

# --------------------------------------------------------------------
# NLP Text Endpoint
# --------------------------------------------------------------------
@app.post("/nlp/text")
async def nlp_from_text(data: dict):
    user_text = (data.get("text", "") or "").strip()
    uid = random.randint(10000, 99999)

    # 1. Classify intent and fuse
    nlp = classify_intent(user_text)
    action = fusion.fuse(nlp)

    # 2. Broadcast both nlp_result and action_result
    result = await broadcast_nlp_and_action(uid, user_text, nlp, action)

    # 3. Return combined response
    return {
        "status": "ok",
        "id": uid,
        "text": user_text,
        "nlp": result["nlp"],
        "action": result["action"]
    }

# --------------------------------------------------------------------
# Action Endpoint (mock/example)
# --------------------------------------------------------------------
@app.post("/action")
async def mock_action():
    payload = {
        "type": "action_result",
        "action": "open_app",
        "slots": {"app": "chrome"},
        "status": "ok",
        "id": 1
    }
    await broadcast(payload)
    return payload

# --------------------------------------------------------------------
# CV / Screen Update
# --------------------------------------------------------------------
@app.post("/cv/update")
async def cv_update(payload: dict):
    fusion.update_cv(payload)
    event = {
        "type": "screen_update",
        "content": payload
    }
    await broadcast(event)
    return {"status": "ok"}

# --------------------------------------------------------------------
# CV Analyze Active Window
# --------------------------------------------------------------------
@app.get("/cv/analyze/active")
async def cv_analyze_active():
    result = screen_analyzer.analyze_active_window(
        capture_screenshot=True,
        detect_text=True,
        get_ui_tree=False
    )

    objects = []
    for det in result.get("text_detections", []):
        objects.append({
            "type": "screen_object",
            "object": det.get("text", "unknown"),
            "confidence": det.get("confidence", 0.0),
            "bbox": det.get("bbox", [0,0,0,0])
        })

    payload = {
        "type": "vision_result",
        "description": f"Active window: {result.get('window_info', {}).get('title', '')}",
        "objects": objects
    }

    # Optionally, broadcast each object as screen_object (Unity-friendly)
    await broadcast(payload)
    for obj in objects:
        await broadcast({
            "type": "screen_object",
            "object_name": obj["object"],
            "confidence": obj["confidence"],
            "bbox": obj["bbox"]
        })

    return payload

# --------------------------------------------------------------------
# CV Analyze All Windows
# --------------------------------------------------------------------
@app.get("/cv/analyze/all")
async def cv_analyze_all():
    result = screen_analyzer.get_desktop_state()
    objects = []
    for win in result.get("all_windows", []):
        objects.append({
            "type": "screen_object",
            "object": win.get("title", "unknown"),
            "confidence": 1.0,
            "bbox": win.get("bbox", [0,0,0,0])
        })

    payload = {
        "type": "vision_result",
        "description": f"{result.get('window_count', 0)} windows detected",
        "objects": objects
    }

    await broadcast(payload)
    for obj in objects:
        await broadcast({
            "type": "screen_object",
            "object_name": obj["object"],
            "confidence": obj["confidence"],
            "bbox": obj["bbox"]
        })

    return payload

# --------------------------------------------------------------------
# CV Analyze Window by Name
# --------------------------------------------------------------------
@app.post("/cv/analyze/window")
async def cv_analyze_window(data: dict):
    name = data.get("name", "")
    result = screen_analyzer.analyze_window(
        name,
        capture_screenshot=True,
        detect_text=True,
        get_ui_tree=False
    )

    objects = []
    for det in result.get("text_detections", []):
        objects.append({
            "type": "screen_object",
            "object": det.get("text", "unknown"),
            "confidence": det.get("confidence", 0.0),
            "bbox": det.get("bbox", [0,0,0,0])
        })

    payload = {
        "type": "vision_result",
        "description": f"Window: {result.get('window_info', {}).get('title', '')}",
        "objects": objects
    }

    await broadcast(payload)
    for obj in objects:
        await broadcast({
            "type": "screen_object",
            "object_name": obj["object"],
            "confidence": obj["confidence"],
            "bbox": obj["bbox"]
        })

    return payload

# --------------------------------------------------------------------
# CV Search by Text
# --------------------------------------------------------------------
@app.post("/cv/search")
async def cv_search(data: dict):
    term = data.get("query", "")
    matches = screen_analyzer.find_window_by_content(term)
    objects = []
    for m in matches:
        objects.append({
            "type": "screen_object",
            "object": m.get("window", {}).get("title", ""),
            "confidence": 1.0,
            "bbox": m.get("window", {}).get("bbox", [0,0,0,0])
        })

    payload = {
        "type": "vision_result",
        "description": f"Search results for '{term}'",
        "objects": objects
    }

    await broadcast(payload)
    for obj in objects:
        await broadcast({
            "type": "screen_object",
            "object_name": obj["object"],
            "confidence": obj["confidence"],
            "bbox": obj["bbox"]
        })

    return payload

# --------------------------------------------------------------------
# CV Summaries
# --------------------------------------------------------------------
@app.get("/cv/summaries")
async def cv_summaries():
    summaries = screen_analyzer.get_all_windows_summary()
    objects = []
    for win in summaries:
        objects.append({
            "type": "screen_object",
            "object": win.get("name", "unknown"),
            "confidence": 1.0,
            "bbox": win.get("bbox", [0,0,0,0])
        })

    payload = {
        "type": "vision_result",
        "description": f"{len(summaries)} window summaries",
        "objects": objects
    }

    await broadcast(payload)
    for obj in objects:
        await broadcast({
            "type": "screen_object",
            "object_name": obj["object"],
            "confidence": obj["confidence"],
            "bbox": obj["bbox"]
        })

    return payload

# --------------------------------------------------------------------
# Bounding Box Endpoint (YOLO)
# --------------------------------------------------------------------
@app.get("/cv/bb")
async def get_bounding_boxes():
    with bb_lock:
        latest = bb_generator.latest_result

    if latest is None:
        payload = {
            "status": "no_data_yet",
            "message": "Model warming up, no detections yet."
        }
        await broadcast(payload)
        return payload
    else:
        objects = []
        for det in latest.get("detections", []):
            objects.append({
                "type": "screen_object",
                "object": det.get("class_name", ""),
                "confidence": det.get("confidence", 0.0),
                "bbox": det.get("bbox", [0,0,0,0])
            })

        payload = {
            "type": "vision_result",
            "description": "Screen detections from YOLO",
            "objects": objects
        }

        await broadcast(payload)
        for obj in objects:
            await broadcast({
                "type": "screen_object",
                "object_name": obj["object"],
                "confidence": obj["confidence"],
                "bbox": obj["bbox"]
            })

        return payload

# --------------------------------------------------------------------
# TTS Endpoint (Kokoro)
# --------------------------------------------------------------------
@app.post("/tts")
async def text_to_speech(data: dict):
    """
    Convert text to natural speech using Kokoro TTS.
    Request: {"text": "Hello world", "voice": "af_heart", "speed": 1.0}
    Response: {"status": "ok", "text": "...", "audio": "base64...", "voice": "af_heart"}
    """
    try:
        text = data.get("text", "").strip()
        voice = data.get("voice", "af_heart")  # Default warm female voice
        speed = data.get("speed", 1.0)
        
        if not text:
            return {"error": "No text provided", "status": "failed"}
        
        # Get TTS instance and synthesize
        tts = get_tts_instance(voice=voice)
        audio_b64 = tts.synthesize_to_base64(text, voice=voice, speed=speed)
        
        return {
            "status": "ok",
            "text": text,
            "audio": audio_b64,
            "voice": voice,
            "format": "wav",
            "sample_rate": 24000
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

if __name__ == "__main__":
    print("🚀 AI Companion Backend (main.py) starting on http://127.0.0.1:5000")
    print("📡 WebSocket endpoint: ws://127.0.0.1:5000/ws")
    print("🎤 TTS endpoint: POST http://127.0.0.1:5000/tts")
    uvicorn.run(app, host="127.0.0.1", port=5000)
