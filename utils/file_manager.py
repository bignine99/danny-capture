from datetime import datetime
from pathlib import Path
from utils.config import ConfigManager
import win32gui
import re

class FileManager:
    def __init__(self):
        self.config = ConfigManager()

    def get_save_directory(self) -> Path:
        save_dir = Path(self.config.get("paths", "save_directory"))
        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir

    def get_active_window_title(self) -> str:
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return "capture"
            # Clean invalid characters for filename
            title = re.sub(r'[\\/*?:"<>|]', "", title)
            # Limit length
            return title[:30].strip()
        except Exception:
            return "capture"

    def generate_filename(self, prefix=None) -> str:
        if prefix is None:
            prefix = self.get_active_window_title()
            
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")
        ext = self.config.get("capture", "image_format").lower()
        
        save_dir = self.get_save_directory()
        
        # Determine sequence number
        seq = 1
        while True:
            filename = f"{prefix}_{date_str}_{time_str}_{seq:03d}.{ext}"
            if not (save_dir / filename).exists():
                return filename
            seq += 1

    def get_new_filepath(self, prefix=None) -> Path:
        return self.get_save_directory() / self.generate_filename(prefix)
