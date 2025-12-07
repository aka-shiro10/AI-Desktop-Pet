"""
UI Inspector Module for Desktop Pet AI
Uses Windows UI Automation to inspect UI elements
"""

import win32gui
import win32process
import psutil
from typing import List, Dict, Optional

# Try importing pywinauto
try:
    from pywinauto import Desktop
    from pywinauto.application import Application
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False
    print("⚠️ pywinauto not available - advanced UI inspection disabled")


class UIInspector:
    """Inspect Windows UI elements using automation APIs"""
    
    def __init__(self):
        if PYWINAUTO_AVAILABLE:
            try:
                self.desktop = Desktop(backend="uia")
                print("✓ UI Automation initialized")
            except Exception as e:
                print(f"⚠️ UI Automation init failed: {e}")
                self.desktop = None
        else:
            self.desktop = None
    
    def get_window_info(self, hwnd: int) -> Dict:
        """Get detailed window information"""
        try:
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            
            # Get process info
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                process_name = process.name()
                exe_path = process.exe()
            except:
                process_name = "Unknown"
                exe_path = "Unknown"
            
            return {
                'hwnd': hwnd,
                'title': title,
                'class': class_name,
                'bbox': rect,
                'pid': pid,
                'process_name': process_name,
                'exe_path': exe_path,
                'visible': win32gui.IsWindowVisible(hwnd),
                'enabled': win32gui.IsWindowEnabled(hwnd)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_ui_tree(self, hwnd: int, max_depth: int = 5) -> List[Dict]:
        """Get UI element hierarchy for window"""
        if not PYWINAUTO_AVAILABLE or not self.desktop:
            return []
        
        elements = []
        
        try:
            # Find window by handle
            window = self.desktop.window(handle=hwnd)
            
            def traverse(element, depth=0):
                if depth > max_depth:
                    return
                
                try:
                    # Get element info
                    info = element.element_info
                    name = info.name if hasattr(info, 'name') else ""
                    control_type = info.control_type if hasattr(info, 'control_type') else "Unknown"
                    
                    # Get bounding box
                    try:
                        rect = element.rectangle()
                        bbox = [rect.left, rect.top, rect.right, rect.bottom]
                    except:
                        bbox = [0, 0, 0, 0]
                    
                    # Only add if has meaningful info
                    if name or control_type != "Unknown":
                        elements.append({
                            'name': name,
                            'type': control_type,
                            'bbox': bbox,
                            'depth': depth,
                            'enabled': element.is_enabled() if hasattr(element, 'is_enabled') else True,
                            'visible': element.is_visible() if hasattr(element, 'is_visible') else True
                        })
                    
                    # Traverse children
                    try:
                        for child in element.children():
                            traverse(child, depth + 1)
                    except:
                        pass
                        
                except Exception as e:
                    pass
            
            traverse(window)
            
        except Exception as e:
            print(f"UI tree error: {e}")
        
        return elements
    
    def find_element(self, hwnd: int, name: str = None, control_type: str = None) -> Optional[Dict]:
        """Find specific UI element by name or type"""
        if not PYWINAUTO_AVAILABLE or not self.desktop:
            return None
        
        try:
            window = self.desktop.window(handle=hwnd)
            
            # Search parameters
            search_kwargs = {}
            if name:
                search_kwargs['title'] = name
            if control_type:
                search_kwargs['control_type'] = control_type
            
            element = window.child_window(**search_kwargs)
            
            if element.exists():
                rect = element.rectangle()
                return {
                    'name': name,
                    'type': control_type,
                    'bbox': [rect.left, rect.top, rect.right, rect.bottom],
                    'enabled': element.is_enabled(),
                    'visible': element.is_visible()
                }
        except:
            pass
        
        return None
    
    def get_focused_window(self) -> Optional[Dict]:
        """Get currently focused/active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            return self.get_window_info(hwnd)
        except:
            return None
    
    def list_all_windows(self) -> List[Dict]:
        """List all visible windows with details"""
        windows = []
        
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append(self.get_window_info(hwnd))
            return True
        
        win32gui.EnumWindows(callback, None)
        return windows
    
    def get_browser_tabs(self, hwnd: int, screenshot=None) -> List[str]:
        """
        Try to extract browser tabs using multiple methods
        
        Args:
            hwnd: Window handle
            screenshot: Optional screenshot to use for OCR fallback
        """
        tabs = []
        
        # Method 1: Try UI Automation first (works for some browsers)
        if PYWINAUTO_AVAILABLE and self.desktop:
            try:
                window = self.desktop.window(handle=hwnd)
                
                def search_tabs(element, depth=0):
                    if depth > 10:
                        return
                    
                    try:
                        control_type = element.element_info.control_type.lower()
                        name = element.element_info.name
                        
                        # Look for actual tab items
                        if 'tabitem' in control_type and name:
                            # Filter out junk
                            if (name not in tabs and 
                                len(name) > 3 and  # Ignore very short names
                                not name.startswith('Active View') and
                                not name.startswith('Tab content')):
                                tabs.append(name)
                        
                        try:
                            for child in element.children():
                                search_tabs(child, depth + 1)
                        except:
                            pass
                    except:
                        pass
                
                search_tabs(window)
                
            except Exception as e:
                pass
        
        # Method 2: If no tabs found and screenshot provided, use OCR on tab bar area
        if len(tabs) == 0 and screenshot is not None:
            try:
                # Get window rectangle
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                
                # Tab bar is usually top 40-80 pixels
                tab_region = screenshot.crop((0, 0, width, 80))
                
                # We'll return a flag to use OCR in the analyzer
                return ['__USE_OCR__']
                
            except:
                pass
        
        return tabs