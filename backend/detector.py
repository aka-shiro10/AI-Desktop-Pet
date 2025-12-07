"""
Content Detector Module for Desktop Pet AI
Uses OCR and CV to detect text and UI elements
"""

import os
import numpy as np
from PIL import Image
from typing import List, Dict, Tuple, Optional
import warnings

# Suppress ALL warnings including PyTorch pin_memory spam
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

# Try importing OCR libraries
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠️ Tesseract not available - install for better OCR")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("⚠️ EasyOCR not available - falling back to Tesseract")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV not available - some features disabled")


class ContentDetector:
    """Detect text and UI elements from screenshots"""
    
    def __init__(self, ocr_engine: str = "easyocr", use_gpu: bool = False):
        """
        Initialize detector
        
        Args:
            ocr_engine: "easyocr", "tesseract", or "both"
            use_gpu: Use GPU for EasyOCR (faster but needs CUDA)
        """
        self.ocr_engine = ocr_engine
        self.easyocr_reader = None
        
        if ocr_engine in ["easyocr", "both"] and EASYOCR_AVAILABLE:
            try:
                # Silence warnings during EasyOCR initialization
                import logging
                logging.getLogger('easyocr').setLevel(logging.ERROR)
                
                self.easyocr_reader = easyocr.Reader(['en'], gpu=use_gpu, verbose=False)
                print("✓ EasyOCR initialized")
            except Exception as e:
                print(f"⚠️ EasyOCR failed to init: {e}")
        
        if ocr_engine in ["tesseract", "both"] and not TESSERACT_AVAILABLE:
            print("⚠️ Tesseract not available")
    
    def detect_text_easyocr(self, image: Image.Image) -> List[Dict]:
        """Detect text using EasyOCR"""
        if not self.easyocr_reader:
            return []
        
        try:
            img_array = np.array(image)
            results = self.easyocr_reader.readtext(img_array)
            
            detections = []
            for bbox, text, confidence in results:
                # Convert bbox to [x1, y1, x2, y2]
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                detections.append({
                    'text': text,
                    'bbox': [
                        int(min(x_coords)),
                        int(min(y_coords)),
                        int(max(x_coords)),
                        int(max(y_coords))
                    ],
                    'confidence': float(confidence),
                    'engine': 'easyocr'
                })
            
            return detections
        except Exception as e:
            print(f"EasyOCR error: {e}")
            return []
    
    def detect_text_tesseract(self, image: Image.Image) -> List[Dict]:
        """Detect text using Tesseract"""
        if not TESSERACT_AVAILABLE:
            return []
        
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            detections = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if text and conf > 0:  # Only include confident detections
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    detections.append({
                        'text': text,
                        'bbox': [x, y, x + w, y + h],
                        'confidence': conf / 100.0,
                        'engine': 'tesseract'
                    })
            
            return detections
        except Exception as e:
            print(f"Tesseract error: {e}")
            return []
    
    def detect_text(self, image: Image.Image) -> List[Dict]:
        """Detect all text in image using available OCR engine"""
        if self.ocr_engine == "easyocr" or (self.ocr_engine == "both" and self.easyocr_reader):
            return self.detect_text_easyocr(image)
        elif self.ocr_engine == "tesseract" or self.ocr_engine == "both":
            return self.detect_text_tesseract(image)
        else:
            return []
    
    def detect_text_in_region(self, image: Image.Image, bbox: Tuple[int, int, int, int]) -> List[Dict]:
        """Detect text in specific region of image"""
        x1, y1, x2, y2 = bbox
        region = image.crop((x1, y1, x2, y2))
        
        detections = self.detect_text(region)
        
        # Adjust coordinates to full image
        for det in detections:
            det['bbox'][0] += x1
            det['bbox'][1] += y1
            det['bbox'][2] += x1
            det['bbox'][3] += y1
        
        return detections
    
    def detect_ui_elements(self, image: Image.Image) -> List[Dict]:
        """Detect UI elements using computer vision"""
        if not CV2_AVAILABLE:
            return []
        
        try:
            # Convert to OpenCV format
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            elements = []
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Filter small noise
                if area < 100:
                    continue
                
                # Classify by aspect ratio
                aspect_ratio = w / h if h > 0 else 0
                
                if 2 < aspect_ratio < 10 and h < 50:
                    element_type = "button"
                elif 0.8 < aspect_ratio < 1.2:
                    element_type = "icon"
                elif aspect_ratio > 10:
                    element_type = "menu_bar"
                else:
                    element_type = "container"
                
                elements.append({
                    'type': element_type,
                    'bbox': [x, y, x + w, y + h],
                    'area': area,
                    'aspect_ratio': aspect_ratio
                })
            
            return elements
        except Exception as e:
            print(f"UI detection error: {e}")
            return []
    
    def extract_visible_text(self, image: Image.Image, confidence_threshold: float = 0.5) -> str:
        """Extract all visible text as single string"""
        detections = self.detect_text(image)
        
        # Filter by confidence
        filtered = [d for d in detections if d['confidence'] >= confidence_threshold]
        
        # Sort by vertical position (top to bottom)
        filtered.sort(key=lambda x: x['bbox'][1])
        
        # Combine text
        return " ".join([d['text'] for d in filtered])