"""
Main Screen Analyzer for Desktop Pet AI
Orchestrates capture, detection, and UI inspection
"""

import time
from typing import Dict, List, Optional
from PIL import Image

from capture import ScreenCapture
from detector import ContentDetector
from ui_inspector import UIInspector


class ScreenAnalyzer:
    """Main orchestrator for screen analysis"""
    
    def __init__(self, ocr_engine: str = "easyocr", use_gpu: bool = False):
        """
        Initialize the analyzer
        
        Args:
            ocr_engine: "easyocr", "tesseract", or "both"
            use_gpu: Use GPU for EasyOCR (faster but needs CUDA)
        """
        print("Initializing Screen Analyzer...")
        self.capture = ScreenCapture()
        self.detector = ContentDetector(ocr_engine=ocr_engine, use_gpu=use_gpu)
        self.inspector = UIInspector()
        print("✓ Screen Analyzer ready!\n")
    
    def _extract_tabs_with_ocr(self, hwnd: int, screenshot: Image, debug=False) -> List[str]:
        """Extract browser tabs using OCR on the tab bar area"""
        try:
            rect = self.inspector.get_window_info(hwnd)['bbox']
            width = rect[2] - rect[0]
            
            # Chrome/Edge tab bar is at pixels 0-40 from top
            # Avoid the address bar (starts around pixel 80+)
            tab_region = screenshot.crop((50, 0, width - 200, 40))
            
            # Debug: Save the region we're OCR-ing
            if debug:
                tab_region.save("debug_tab_region.png")
                print(f"   [DEBUG] Saved tab region to debug_tab_region.png")
            
            # Use OCR to detect text in tab bar ONLY
            detections = self.detector.detect_text(tab_region)
            
            # Sort by horizontal position (tabs are left to right)
            detections.sort(key=lambda x: x['bbox'][0])
            
            tabs = []
            last_x = -100  # Track position to avoid duplicates
            
            for det in detections:
                text = det['text'].strip()
                x_pos = det['bbox'][0]
                
                # Tabs should be:
                # 1. At least some distance apart (not same text repeated)
                # 2. Short-ish (not full sentences from page content)
                # 3. Not UI elements
                if (text and 
                    2 < len(text) < 60 and  # Reasonable tab title length
                    x_pos - last_x > 30 and  # At least 30px apart (new tab)
                    text not in ['×', '+', '...', 'New Tab', 'Google', 'Chrome'] and
                    not text.startswith('http') and
                    not text.startswith('www')):
                    
                    tabs.append(text)
                    last_x = x_pos
            
            # If we got nothing, try a slightly different region
            if len(tabs) == 0:
                tab_region = screenshot.crop((80, 5, width - 150, 35))
                
                if debug:
                    tab_region.save("debug_tab_region_alt.png")
                    print(f"   [DEBUG] Saved alternative region to debug_tab_region_alt.png")
                
                detections = self.detector.detect_text(tab_region)
                detections.sort(key=lambda x: x['bbox'][0])
                
                for det in detections:
                    text = det['text'].strip()
                    if text and 2 < len(text) < 60:
                        tabs.append(text)
            
            return tabs[:15]  # Return max 15 tabs
            
        except Exception as e:
            return []
    
    def get_desktop_state(self) -> Dict:
        """Get complete desktop state - all windows and active window"""
        all_windows = self.capture.get_all_windows()
        active_window = self.inspector.get_focused_window()
        
        return {
            'timestamp': time.time(),
            'all_windows': all_windows,
            'active_window': active_window,
            'window_count': len(all_windows)
        }
    
    def analyze_window(self, window_identifier: str, capture_screenshot: bool = True, 
                       detect_text: bool = True, get_ui_tree: bool = False) -> Dict:
        """
        Analyze a specific window
        
        Args:
            window_identifier: Window title or substring
            capture_screenshot: Capture window image
            detect_text: Run OCR on window
            get_ui_tree: Get UI element hierarchy (slower)
        
        Returns:
            Dictionary with window analysis results
        """
        # Find window
        hwnd = self.capture.find_window(window_identifier)
        
        if not hwnd:
            return {
                'error': f"Window '{window_identifier}' not found",
                'available_windows': [w['title'] for w in self.capture.get_all_windows()]
            }
        
        # Get basic window info
        window_info = self.inspector.get_window_info(hwnd)
        result = {
            'window_info': window_info,
            'timestamp': time.time()
        }
        
        # Capture screenshot if requested
        if capture_screenshot:
            screenshot = self.capture.capture_window(hwnd)
            if screenshot:
                result['screenshot'] = screenshot
                result['screenshot_size'] = screenshot.size
                
                # Detect text if requested
                if detect_text:
                    text_detections = self.detector.detect_text(screenshot)
                    result['text_detections'] = text_detections
                    result['extracted_text'] = " ".join([d['text'] for d in text_detections])
            else:
                result['screenshot_error'] = "Failed to capture window"
        
        # Get UI tree if requested
        if get_ui_tree:
            ui_elements = self.inspector.get_ui_tree(hwnd)
            result['ui_elements'] = ui_elements
            result['ui_element_count'] = len(ui_elements)
        
        # Try to get browser tabs
        tabs = self.inspector.get_browser_tabs(hwnd, screenshot if capture_screenshot else None)
        
        # If tabs method returned OCR flag, use OCR on tab bar
        if tabs == ['__USE_OCR__'] and screenshot:
            tabs = self._extract_tabs_with_ocr(hwnd, screenshot, debug=True)
        
        if tabs:
            result['browser_tabs'] = tabs
        
        return result
    
    def analyze_active_window(self, **kwargs) -> Dict:
        """Analyze currently active/focused window"""
        active = self.inspector.get_focused_window()
        
        if not active or not active.get('title'):
            return {'error': 'No active window found'}
        
        return self.analyze_window(active['title'], **kwargs)
    
    def analyze_full_screen(self, monitor_num: int = 1, detect_text: bool = True,
                           detect_ui: bool = False) -> Dict:
        """
        Analyze entire screen using computer vision
        
        Args:
            monitor_num: Monitor number (1 = primary)
            detect_text: Run OCR on screen
            detect_ui: Detect UI elements with CV
        
        Returns:
            Dictionary with screen analysis results
        """
        # Capture full screen
        screenshot = self.capture.capture_full_screen(monitor_num)
        
        result = {
            'timestamp': time.time(),
            'monitor_num': monitor_num,
            'screenshot_size': screenshot.size,
            'screenshot': screenshot
        }
        
        # Detect text
        if detect_text:
            text_detections = self.detector.detect_text(screenshot)
            result['text_detections'] = text_detections
            result['text_count'] = len(text_detections)
            result['extracted_text'] = " ".join([d['text'] for d in text_detections])
        
        # Detect UI elements
        if detect_ui:
            ui_elements = self.detector.detect_ui_elements(screenshot)
            result['ui_elements'] = ui_elements
            result['ui_element_count'] = len(ui_elements)
        
        return result
    
    def find_window_by_content(self, search_text: str) -> List[Dict]:
        """Find windows containing specific text"""
        results = []
        all_windows = self.capture.get_all_windows()
        
        for window in all_windows:
            try:
                screenshot = self.capture.capture_window(window['hwnd'])
                if screenshot:
                    extracted = self.detector.extract_visible_text(screenshot)
                    
                    if search_text.lower() in extracted.lower():
                        results.append({
                            'window': window,
                            'matching_text': extracted
                        })
            except:
                pass
        
        return results
    
    def get_window_summary(self, window_identifier: str) -> Dict:
        """Get quick summary of a window (for NLP processing)"""
        result = self.analyze_window(
            window_identifier,
            capture_screenshot=True,
            detect_text=True,
            get_ui_tree=False
        )
        
        if 'error' in result:
            return result
        
        # Create NLP-friendly summary
        window_info = result['window_info']
        
        summary = {
            'window_name': window_info['title'],
            'application': window_info['process_name'],
            'visible_text': result.get('extracted_text', ''),
            'browser_tabs': result.get('browser_tabs', []),
            'is_active': window_info.get('enabled', False),
            'position': window_info['bbox']
        }
        
        return summary
    
    def get_all_windows_summary(self) -> List[Dict]:
        """Get summary of all open windows (for NLP)"""
        windows = self.capture.get_all_windows()
        
        summaries = []
        for window in windows:
            info = self.inspector.get_window_info(window['hwnd'])
            summaries.append({
                'name': info['title'],
                'application': info['process_name'],
                'hwnd': window['hwnd']
            })
        
        return summaries