"""
Screen Capture Module for Desktop Pet AI
Handles all screenshot operations for windows and full screen
"""

import mss
import numpy as np
from PIL import Image
import win32gui
import win32ui
import win32con
from typing import Optional, Tuple, List

class ScreenCapture:
    """High-performance screen capture with window targeting"""
    
    def __init__(self):
        self.sct = mss.mss()
    
    def get_all_windows(self) -> List[dict]:
        """Get all visible windows with their info"""
        windows = []
        
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:  # Only include windows with titles
                    try:
                        rect = win32gui.GetWindowRect(hwnd)
                        windows.append({
                            'hwnd': hwnd,
                            'title': title,
                            'bbox': rect,
                            'class': win32gui.GetClassName(hwnd)
                        })
                    except:
                        pass
            return True
        
        win32gui.EnumWindows(callback, None)
        return windows
    
    def find_window(self, title_substring: str) -> Optional[int]:
        """Find window handle by title (case-insensitive)"""
        title_substring = title_substring.lower()
        
        def callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if title_substring in window_title.lower():
                    results.append(hwnd)
            return True
        
        results = []
        win32gui.EnumWindows(callback, results)
        return results[0] if results else None
    
    def capture_window(self, hwnd: int) -> Optional[Image.Image]:
        """Capture specific window by handle"""
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                return None
            
            monitor = {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }
            
            screenshot = self.sct.grab(monitor)
            return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        except Exception as e:
            print(f"Error capturing window: {e}")
            return None
    
    def capture_full_screen(self, monitor_num: int = 1) -> Image.Image:
        """Capture entire monitor"""
        screenshot = self.sct.grab(self.sct.monitors[monitor_num])
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Image.Image:
        """Capture specific screen region"""
        monitor = {"left": x, "top": y, "width": width, "height": height}
        screenshot = self.sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    
    def get_active_window(self) -> Optional[dict]:
        """Get currently focused window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            
            return {
                'hwnd': hwnd,
                'title': title,
                'bbox': rect,
                'class': win32gui.GetClassName(hwnd)
            }
        except:
            return None