# fusion.py

import time
import platform
import subprocess
import webbrowser


# ======================================================================
# ACTION EXECUTOR (URL-based + Chrome launcher)
# ======================================================================
class ActionExecutor:

    # ------------------------------------------------------------
    # OPEN APPLICATION / WEBSITE
    # ------------------------------------------------------------
    def open(self, app: str):
        app = app.lower()

        # Mapping apps → URLs or executables
        url_map = {
            "youtube": "https://www.youtube.com",
            "whatsapp": "https://web.whatsapp.com",
            "chatgpt": "https://chat.openai.com",
            "music": "https://soundcloud.com"
        }

        # Special case: Chrome
        if app == "chrome":
            return self.open_chrome()

        # Normal URLs
        if app in url_map:
            try:
                webbrowser.open(url_map[app])
                return f"Opening {app}."
            except Exception as e:
                return f"Failed to open {app}: {e}"

        return f"No mapping available for app '{app}'."

    # ------------------------------------------------------------
    # OPEN GOOGLE CHROME (system dependent)
    # ------------------------------------------------------------
    def open_chrome(self):
        system = platform.system().lower()

        try:
            if system == "windows":
                subprocess.Popen([
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                ])
                return "Opening Chrome."

            if system == "darwin":  # macOS
                subprocess.Popen(["open", "-a", "Google Chrome"])
                return "Opening Chrome."

            if system == "linux":
                subprocess.Popen(["google-chrome"])
                return "Opening Chrome."

        except Exception as e:
            return f"Failed to open Chrome: {e}"

        return "Unsupported operating system."

    # ------------------------------------------------------------
    # CLOSE CURRENT TAB
    # ------------------------------------------------------------
    def close_current_tab(self):
        system = platform.system().lower()

        try:
            if system == "windows":
                subprocess.Popen(["powershell", "-Command",
                    "(new-object -com wscript.shell).SendKeys('^w')"])
                return "Closing the current tab."

            if system == "darwin":
                subprocess.Popen(["osascript", "-e",
                    'tell application "System Events" to keystroke "w" using command down'])
                return "Closing the current tab."

            if system == "linux":
                subprocess.Popen(["xdotool", "key", "ctrl+w"])
                return "Closing the current tab."

        except Exception as e:
            return f"Failed to close tab: {e}"

        return "Unsupported OS."

    # ------------------------------------------------------------
    # CLOSE ALL WINDOWS (safe shortcut)
    # ------------------------------------------------------------
    def close_all_windows(self):
        system = platform.system().lower()

        try:
            if system == "windows":
                subprocess.Popen(["powershell", "-Command",
                    "(new-object -com wscript.shell).SendKeys('%{F4}')"])
                return "Closing all windows."

            if system == "darwin":
                subprocess.Popen(["osascript", "-e",
                    'tell application "System Events" to keystroke "q" using command down'])
                return "Closing all windows."

            if system == "linux":
                subprocess.Popen(["xdotool", "key", "alt+F4"])
                return "Closing all windows."

        except Exception as e:
            return f"Failed: {e}"

        return "Unsupported OS."

    # ------------------------------------------------------------
    # PLAY MUSIC → SOUNDLOUD.COM
    # ------------------------------------------------------------
    def play_music(self):
        try:
            webbrowser.open("https://soundcloud.com")
            return "Opening SoundCloud."
        except Exception as e:
            return f"Failed to open SoundCloud: {e}"

    # ------------------------------------------------------------
    # DESCRIBE SCREEN (CV)
    # ------------------------------------------------------------
    def describe(self, cv_state):
        if not cv_state:
            return "I have no screen data yet."
        return f"I see: {cv_state}"


# ======================================================================
# FUSION MODULE — NLP + CV + ACTION EXECUTION
# ======================================================================
class FusionModule:
    def __init__(self):
        self.cv_state = None
        self.last_cv_update = 0
        self.actions = ActionExecutor()

    def update_cv(self, data: dict):
        self.cv_state = data
        self.last_cv_update = time.time()

    # ---------------------------------------------------------------
    # MAIN LOGIC
    # ---------------------------------------------------------------
    def fuse(self, nlp: dict):

        intent = (nlp.get("intent") or "").lower()
        slots = nlp.get("slots", {})
        reply = nlp.get("reply", "")

        # ========= OPEN APP (URL-based) =========
        if intent.startswith("open "):
            if "app" in slots:
                result = self.actions.open(slots["app"])
                return {
                    "action": "open_app",
                    "slots": slots,
                    "reply": result
                }

        # ========= CLOSE CURRENT TAB =========
        if intent == "close current tab":
            result = self.actions.close_current_tab()
            return {
                "action": "close_current_tab",
                "slots": {},
                "reply": result
            }

        # ========= CLOSE ALL WINDOWS =========
        if intent == "close all windows":
            result = self.actions.close_all_windows()
            return {
                "action": "close_all_windows",
                "slots": {},
                "reply": result
            }

        # ========= PLAY MUSIC (SoundCloud) =========
        if intent == "play music":
            result = self.actions.play_music()
            return {
                "action": "play_music",
                "slots": {},
                "reply": result
            }

        # ========= WHAT’S ON SCREEN? (CV) =========
        if intent == "whats on screen":
            result = self.actions.describe(self.cv_state)
            return {
                "action": "describe_screen",
                "slots": {"screen_state": self.cv_state},
                "reply": result
            }

        # ========= DEFAULT =========
        return {
            "action": "none",
            "slots": {},
            "reply": reply
        }


# Global instance for imports
fusion = FusionModule()
