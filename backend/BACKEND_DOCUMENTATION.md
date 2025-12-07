# AI Companion Backend - Complete Documentation

**Project Type:** Final Year Project (FYP)  
**Backend:** FastAPI + WebSocket  
**Technology Stack:** Python 3.13, NLP, Computer Vision, Screen Automation

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Module Overview](#module-overview)
3. [API Endpoints](#api-endpoints)
4. [Setup & Installation](#setup--installation)
5. [Running the Server](#running-the-server)
6. [Integration Guide](#integration-guide)
7. [Troubleshooting](#troubleshooting)

---

## 🏗️ System Architecture

The backend is a **multi-modal AI system** combining NLP and Computer Vision for intelligent desktop automation:

```
┌──────────────────────────────────────────────────────────────┐
│                     FastAPI Server (Port 8000)               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Real-time Communication Layer              │ │
│  │  • WebSocket (/ws) - Bidirectional streaming           │ │
│  │  • REST Endpoints - Synchronous API calls              │ │
│  │  • CORS Enabled - Compatible with all clients          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │  NLP Pipeline    │  │ Computer Vision  │  │  Action    │ │
│  │                  │  │     Pipeline     │  │  Executor  │ │
│  ├──────────────────┤  ├──────────────────┤  ├────────────┤ │
│  │ • STT (Whisper)  │  │ • Screen Capture │  │ • Fusion   │ │
│  │ • Intent Classi. │  │ • Text Detection │  │ • Automati │ │
│  │ • Preprocessing  │  │ • UI Inspection  │  │ • URL Open │ │
│  └──────────────────┘  └──────────────────┘  └────────────┘ │
│           ↓                    ↓                      ↓       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ Sentence Trans.  │  │ YOLO Detector    │  │ WebBrowser │ │
│  │ Intent Detection │  │ Bounding Boxes   │  │ Subprocess │ │
│  │ all-MiniLM-L6-v2 │  │ best.onnx model  │  │ Operations │ │
│  └──────────────────┘  └──────────────────┘  └────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input (Voice/Text)
    ↓
[STT Module] → Transcribe to text
    ↓
[Intent Engine] → Classify intent (e.g., "open youtube")
    ↓
[Fusion Module] → Map to action (URL, app launch, etc.)
    ↓
[Action Executor] → Execute on Windows
    ↓
[WebSocket/REST] → Send result to client
```

---

## 📦 Module Overview

### 1. **main.py** - Server Core

**Purpose:** FastAPI application entry point

**Key Components:**

- **FastAPI App:** Initializes with CORS middleware for cross-origin requests
- **YOLO Thread:** Background process running object detection every 5 seconds
- **Screen Analyzer:** Initializes screen analysis tools
- **WebSocket Handler:** Manages real-time client connections
- **REST Endpoints:** All API routes defined here

**Key Variables:**

- `app` - FastAPI application instance
- `bb_generator` - YOLO detector for bounding boxes
- `screen_analyzer` - Screen analysis orchestrator
- `connections` - Set of active WebSocket connections

### 2. **stt.py** - Speech-to-Text

**Purpose:** Convert audio to text using Whisper

**Model:** OpenAI Whisper "tiny" (71MB, fast but accurate)

**Main Function:**

```python
def transcribe_wav(file_bytes: bytes) -> str:
    """Convert WAV bytes → text"""
    # Writes bytes to temp file
    # Runs Whisper transcription
    # Returns extracted text
```

**Features:**

- ✅ Automatic model download on first run
- ✅ Fast inference with "tiny" model
- ✅ Supports English language transcription
- ✅ GPU-friendly (no dependencies on hardware)

### 3. **intent_engine.py** - NLP Intent Classification

**Purpose:** Understand user commands

**Model:** SentenceTransformers "all-MiniLM-L6-v2" (22MB)

**Key Components:**

- **Preprocessing:** Lowercase, remove punctuation, lemmatize, remove stopwords
- **Command Database:** 8+ predefined intents with variations
- **Semantic Matching:** Cosine similarity-based classification
- **Keyword Boosting:** Enhanced detection for command keywords

**Supported Commands:**

```
open_youtube       → "open youtube", "go to youtube", "launch youtube"
open_chrome        → "open chrome", "launch chrome"
open_whatsapp      → "open whatsapp", "launch whatsapp"
open_chatgpt       → "open chatgpt", "go to chatgpt"
close_current_tab  → "close current tab", "shut this tab"
close_all_windows  → "close all windows", "shut everything"
play_music         → "play music", "start music", "play some music"
whats_on_screen    → "what's on screen", "describe the screen"
```

**Output Format:**

```python
{
    "intent": "open_youtube",
    "confidence": 0.95,
    "slots": {"app": "youtube"},
    "raw_text": "hey open youtube for me"
}
```

### 4. **analyzer.py** - Screen Analysis Orchestrator

**Purpose:** Analyze desktop, windows, and extract information

**Main Class:** `ScreenAnalyzer`

**Key Methods:**

- `get_desktop_state()` - Get all open windows and active window
- `analyze_active_window()` - Analyze currently focused window
- `analyze_window(name)` - Analyze specific window
- `find_window_by_content(search_text)` - Find window with specific text
- `get_all_windows_summary()` - Quick summary of all windows
- `analyze_full_screen()` - Full screen analysis with OCR

**Features:**

- ✅ Window enumeration (Windows API)
- ✅ Screenshot capture
- ✅ OCR text detection (EasyOCR)
- ✅ UI element detection
- ✅ Browser tab extraction
- ✅ Content searching

### 5. **capture.py** - Screen/Window Capture

**Purpose:** High-performance screen capture

**Main Class:** `ScreenCapture`

**Key Methods:**

- `get_all_windows()` - Enumerate all visible windows
- `find_window(title)` - Find window by title substring
- `capture_window(hwnd)` - Screenshot a specific window
- `capture_full_screen()` - Screenshot entire monitor
- `capture_region(x, y, w, h)` - Screenshot specific area
- `get_active_window()` - Get currently focused window

**Technology:** MSS (fast) + PIL (image format conversion)

### 6. **detector.py** - OCR & Object Detection

**Purpose:** Extract text and detect UI elements

**Main Class:** `ContentDetector`

**OCR Engines:**

- **EasyOCR** - High accuracy, slower
- **Tesseract** - Fast, lower accuracy (if installed)

**Key Methods:**

- `detect_text(image)` - Extract all text from image
- `detect_text_in_region(image, bbox)` - OCR specific region
- `detect_ui_elements(image)` - Detect buttons, fields, etc.
- `extract_visible_text(image)` - Get concatenated text

**Output:**

```python
{
    'text': 'detected text',
    'bbox': [x1, y1, x2, y2],  # bounding box
    'confidence': 0.95
}
```

### 7. **ui_inspector.py** - Windows UI Automation

**Purpose:** Interact with Windows UI elements

**Technology:** pywinauto + pywin32

**Key Functions:**

- Get UI element tree
- Get browser tabs (Chrome/Edge)
- Click elements
- Get window properties
- Send keyboard input

### 8. **bb_generation.py** - YOLO Object Detection

**Purpose:** Continuous object detection from screen

**Model:** ONNX format (best.onnx)

**Key Methods:**

- `screenshot()` - Grab desktop screenshot
- `run_detection(frame)` - Run YOLO on frame
- `start()` - Start continuous detection

**Background Thread:**

- Runs every 5 seconds
- Stores latest detections
- Non-blocking (daemon thread)

**Output Format:**

```python
{
    'timestamp': 1701953400.123,
    'count': 5,
    'detections': [
        {
            'bbox': [x, y, width, height],
            'confidence': 0.92,
            'class_id': 0,
            'class_name': 'person'
        }
    ]
}
```

### 9. **fusion.py** - Action Executor

**Purpose:** Convert intents to actions

**Main Class:** `ActionExecutor`

**Key Methods:**

- `open(app)` - Open application or website
- `open_chrome()` - Launch Google Chrome
- `close_browser()` - Close browser window
- `play_pause_media()` - Media control

**URL Mapping:**

```python
youtube    → https://www.youtube.com
whatsapp   → https://web.whatsapp.com
chatgpt    → https://chat.openai.com
chrome     → subprocess call
```

**Also Contains:**

- `fusion` - Global instance for use in main.py
- `update_cv()` - Update CV context

---

## 🔌 API Endpoints

### **Root Endpoint**

```
GET /
```

Returns server info and list of all endpoints

**Response:**

```json
{
    "message": "AI Companion Backend",
    "status": "running",
    "endpoints": { ... }
}
```

### **Health Check**

```
GET /health
```

Quick server status check

### **WebSocket - Real-time Connection**

```
WS /ws
```

Bidirectional communication for real-time updates

**Client → Server:**

- Any text (ping/heartbeat)

**Server → Broadcast:**

```json
{
  "type": "action_result",
  "id": 12345,
  "text": "open youtube",
  "intent": "open_youtube",
  "slots": { "app": "youtube" },
  "reply": "Opening youtube.",
  "status": "ok"
}
```

### **NLP Endpoints**

#### **1. Voice Intent Processing**

```
POST /nlp/voice
Content-Type: multipart/form-data
```

**Body:**

- `file` - WAV audio file

**Process:**

1. Transcribe audio → text (Whisper)
2. Classify intent (SentenceTransformers)
3. Execute action (Fusion)
4. Broadcast result via WebSocket

**Response:**

```json
{
  "type": "action_result",
  "id": 45678,
  "text": "open chrome",
  "intent": "open_chrome",
  "slots": { "app": "chrome" },
  "reply": "Opening Chrome.",
  "status": "ok"
}
```

#### **2. Text Intent Processing**

```
POST /nlp/text
Content-Type: application/json
```

**Body:**

```json
{
  "text": "open youtube"
}
```

**Response:** Same as voice endpoint

#### **3. Mock Action**

```
POST /action
```

Test endpoint for action execution

### **Computer Vision Endpoints**

#### **1. Analyze Active Window**

```
GET /cv/analyze/active
```

Analyze currently focused window

**Response:**

```json
{
  "type": "vision_result",
  "description": "Active window: Google Chrome",
  "objects": [
    {
      "type": "screen_object",
      "object": "Search box text",
      "confidence": 0.98,
      "bbox": [100, 50, 400, 70]
    }
  ]
}
```

#### **2. Analyze All Windows**

```
GET /cv/analyze/all
```

Get all open windows

#### **3. Analyze Specific Window**

```
POST /cv/analyze/window
Content-Type: application/json
```

**Body:**

```json
{
  "name": "Chrome"
}
```

#### **4. Search Windows by Content**

```
POST /cv/search
Content-Type: application/json
```

**Body:**

```json
{
  "query": "login"
}
```

Finds windows containing the search term

#### **5. Get Window Summaries**

```
GET /cv/summaries
```

Quick summary of all windows

#### **6. YOLO Bounding Boxes**

```
GET /cv/bb
```

Latest object detections from YOLO

**Response:**

```json
{
  "type": "vision_result",
  "description": "Screen detections from YOLO",
  "objects": [
    {
      "type": "screen_object",
      "object": "person",
      "confidence": 0.92,
      "bbox": [120, 80, 400, 600]
    }
  ]
}
```

#### **7. CV Update**

```
POST /cv/update
Content-Type: application/json
```

Update CV context

---

## 🚀 Setup & Installation

### **Prerequisites**

- Python 3.13 (recommended)
- Windows 10/11 (for Windows API)
- 4GB RAM (minimum)
- Internet connection (first run to download models)

### **Step 1: Install Dependencies**

```bash
cd "d:\fyp\New folder\NLP CV Project"
pip install -r requirements.txt
```

**Key Packages:**
| Package | Purpose | Size |
|---------|---------|------|
| fastapi | Web framework | - |
| uvicorn | ASGI server | - |
| openai-whisper | Speech recognition | 71MB |
| sentence-transformers | NLP intent | 22MB |
| torch | Deep learning | 500MB+ |
| ultralytics | YOLO detection | 50MB+ |
| easyocr | Text OCR | 100MB+ |
| pywinauto | Windows automation | - |

### **Step 2: Download Spacy Model**

```bash
python -m spacy download en_core_web_sm
```

### **Step 3: Install Tesseract (Optional)**

For faster OCR without GPU:

1. Download: https://github.com/UB-Mannheim/tesseract-ocr-w64
2. Install to default location
3. No additional Python setup needed

### **Step 4: Verify Installation**

```bash
# Test imports
python -c "import torch; import whisper; import sentence_transformers; print('✅ All packages OK')"
```

---

## ▶️ Running the Server

### **Option 1: Using Full Python Path (Recommended)**

```bash
C:\Users\akasu\AppData\Local\Programs\Python\Python313\python.exe -m uvicorn main:app --reload
```

### **Option 2: Using Batch File**

Create `run.bat`:

```batch
@echo off
C:\Users\akasu\AppData\Local\Programs\Python\Python313\python.exe -m uvicorn main:app --reload
pause
```

Then double-click `run.bat`

### **Option 3: Using PowerShell**

```powershell
C:\Users\akasu\AppData\Local\Programs\Python\Python313\python.exe -m uvicorn main:app --reload
```

### **Server Output**

```
INFO:     Will watch for changes in these directories: ['D:\\fyp\\New folder\\NLP CV Project']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [1908] using StatReload
🔥 YOLO bounding box generator started in background
Initializing Screen Analyzer...
✓ EasyOCR initialized
✓ UI Automation initialized
✓ Screen Analyzer ready!
```

### **Verify Server is Running**

1. **Browser:** Visit http://127.0.0.1:8000/
2. **API Docs:** Visit http://127.0.0.1:8000/docs
3. **Health Check:** Visit http://127.0.0.1:8000/health

---

## 🔗 Integration Guide

### **For Frontend/Client Integration**

#### **1. WebSocket Connection (Recommended for Real-time)**

```javascript
// JavaScript Example
const ws = new WebSocket("ws://127.0.0.1:8000/ws");

ws.onopen = () => console.log("Connected");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Action Result:", data);
  // Update UI with data
};
```

#### **2. REST API - Voice Command**

```javascript
// Send audio to backend
const formData = new FormData();
formData.append("file", audioBlob, "audio.wav");

fetch("http://127.0.0.1:8000/nlp/voice", {
  method: "POST",
  body: formData,
})
  .then((r) => r.json())
  .then((data) => console.log(data));
```

#### **3. REST API - Text Command**

```javascript
// Send text command
fetch("http://127.0.0.1:8000/nlp/text", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: "open youtube" }),
})
  .then((r) => r.json())
  .then((data) => console.log(data));
```

#### **4. REST API - Screen Analysis**

```javascript
// Get active window analysis
fetch("http://127.0.0.1:8000/cv/analyze/active")
  .then((r) => r.json())
  .then((data) => console.log(data));

// Get YOLO detections
fetch("http://127.0.0.1:8000/cv/bb")
  .then((r) => r.json())
  .then((data) => console.log(data));
```

### **For Unity Integration**

```csharp
using UnityEngine;
using UnityEngine.Networking;

public class BackendClient : MonoBehaviour {
    private string baseUrl = "http://127.0.0.1:8000";

    public void SendTextCommand(string text) {
        StartCoroutine(PostCommand(text));
    }

    IEnumerator PostCommand(string text) {
        var json = JsonUtility.ToJson(new { text = text });
        using (UnityWebRequest request = UnityWebRequest.Post(
            baseUrl + "/nlp/text",
            "application/json")) {
            request.uploadHandler = new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(json));
            yield return request.SendWebRequest();
            var response = request.downloadHandler.text;
            ProcessResponse(response);
        }
    }
}
```

---

## 🐛 Troubleshooting

### **Issue: "Not Found" Error**

**Cause:** Accessing root without endpoint defined
**Solution:** Already fixed - endpoints now return proper responses

### **Issue: ModuleNotFoundError for tf-keras**

**Cause:** Wrong Python version (3.10 vs 3.13)
**Solution:** Use full Python 3.13 path or set as default in PATH

### **Issue: YOLO/ONNX Error**

**Cause:** Missing ONNX runtime
**Solution:** Install via pip

```bash
pip install onnx onnxruntime
```

### **Issue: EasyOCR Takes Forever**

**Cause:** First time model download
**Solution:** Normal - models cache after first run. Subsequent calls are fast.

### **Issue: Tesseract Not Found**

**Cause:** pytesseract can't locate Tesseract
**Solution:** Install from https://github.com/UB-Mannheim/tesseract-ocr-w64

### **Issue: pywin32 COM Errors**

**Cause:** Post-install scripts not run
**Solution:**

```bash
python -m pywin32_postinstall -install
```

### **Issue: Port 8000 Already in Use**

**Cause:** Server already running or another app using port
**Solution:**

```bash
# Run on different port
uvicorn main:app --port 8001 --reload
```

### **Issue: No Windows API Available**

**Cause:** Running on non-Windows
**Solution:** Some features disabled on Linux/Mac - CV endpoints won't work

---

## 📊 Performance Metrics

| Component             | Latency    | Notes                          |
| --------------------- | ---------- | ------------------------------ |
| STT (Whisper)         | 2-5s       | Depends on audio length        |
| Intent Classification | 50-100ms   | Very fast                      |
| Screen Capture        | 20-50ms    | Depends on resolution          |
| OCR (EasyOCR)         | 1-3s       | First run slower               |
| YOLO Detection        | 500-1000ms | Running every 5s in background |
| WebSocket Broadcast   | <10ms      | Per client                     |

---

## 📚 Additional Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Whisper Documentation:** https://github.com/openai/whisper
- **Sentence Transformers:** https://www.sbert.net/
- **EasyOCR:** https://github.com/JaidedAI/EasyOCR
- **YOLO (Ultralytics):** https://docs.ultralytics.com/

---

## 👤 Author Notes

This backend is designed for:

- ✅ **Real-time voice/text commands** to control desktop
- ✅ **Screen understanding** with OCR and object detection
- ✅ **100% offline** operation (no cloud APIs)
- ✅ **Extensible** - easy to add new commands/intents
- ✅ **Production-ready** - proper error handling and logging

For questions or issues, check the troubleshooting section or review the module documentation above.

---

**Last Updated:** December 7, 2025  
**Status:** ✅ Working & Ready for Integration
