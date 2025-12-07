# Desktop Pet AI - Screen Analyzer Installation Guide

## Prerequisites

1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/

2. **Tesseract OCR** (for text detection)
   - Download installer: https://github.com/UB-Mannheim/tesseract/wiki
   - During installation, note the installation path
   - Add to PATH or set in code

## Installation Steps

### Step 1: Fix NumPy Compatibility (IMPORTANT!)

EasyOCR requires NumPy < 2.0. Install this FIRST:

```bash
pip install "numpy<2"
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Verify Installation

Run this to test all imports:

```bash
python -c "import numpy, cv2, easyocr, mss, PIL, win32gui, pywinauto, psutil; print('✓ All imports successful!')"
```

## Troubleshooting

### Common Issues

#### 1. NumPy Version Conflict

**Error:** `AttributeError: module 'numpy' has no attribute 'float_'`

**Solution:**
```bash
pip uninstall numpy opencv-python easyocr -y
pip install "numpy<2"
pip install opencv-python easyocr
```

#### 2. Tesseract Not Found

**Error:** `TesseractNotFoundError`

**Solution:**
- Install Tesseract from the link above
- Add to PATH, or set in code:
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

#### 3. EasyOCR Takes Forever to Load

**Solution:** This is normal the first time - it downloads language models. Subsequent runs are faster.

#### 4. OpenCV Import Error

**Solution:**
```bash
pip uninstall opencv-python opencv-python-headless -y
pip install opencv-python==4.8.1.78
```

#### 5. PyWin32 COM Error

**Solution:**
```bash
python -m pywin32_postinstall -install
```

## GPU Acceleration (Optional)

For faster OCR with EasyOCR on NVIDIA GPUs:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

Then in your code:
```python
analyzer = ScreenAnalyzer(ocr_engine="easyocr", use_gpu=True)
```

## Usage

### Quick Test

```bash
python demo.py
```

### Basic Usage

```python
from analyzer import ScreenAnalyzer

# Initialize
analyzer = ScreenAnalyzer()

# Get all open windows
state = analyzer.get_desktop_state()
print(f"Found {state['window_count']} windows")

# Analyze specific window
result = analyzer.analyze_window("Chrome", detect_text=True)
print(result['extracted_text'])

# Analyze active window
active = analyzer.analyze_active_window()
```

## Performance Tips

1. **Use Tesseract for speed** (if you don't need high accuracy):
   ```python
   analyzer = ScreenAnalyzer(ocr_engine="tesseract")
   ```

2. **Disable OCR when not needed**:
   ```python
   result = analyzer.analyze_window("Chrome", detect_text=False)
   ```

3. **Use GPU if available**:
   ```python
   analyzer = ScreenAnalyzer(use_gpu=True)
   ```

## Next Steps

The analyzer is ready to integrate with your:
- **NLP module** - Use `get_window_summary()` and `get_all_windows_summary()` 
- **Unity component** - Send analysis results via JSON
- **Voice commands** - Parse window names and perform actions

## File Structure

```
screen_analyzer/
├── analyzer.py          # Main orchestrator
├── capture.py           # Screen/window capture
├── detector.py          # OCR and CV detection
├── ui_inspector.py      # Windows UI automation
├── demo.py              # Test script
├── requirements.txt     # Dependencies
└── INSTALLATION.md      # This file
```

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Verify all dependencies are installed: `pip list`
3. Run the demo script to test: `python demo.py`