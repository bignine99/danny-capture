import json
import os
from pathlib import Path
import platform

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        # Determine AppData directory
        if platform.system() == "Windows":
            app_data = Path(os.environ.get('APPDATA', str(Path.home())))
        else:
            app_data = Path.home() / ".config"
            
        self.app_dir = app_data / "Danny_Capture"
        self.config_file = self.app_dir / "config.json"
        
        self.default_config = {
            "capture": {
                "default_mode": "간편 캡쳐",
                "auto_save": True,
                "auto_copy_clipboard": True,
                "show_editor": True,
                "delay_seconds": 0,
                "image_format": "PNG"
            },
            "paths": {
                "save_directory": str(Path.home() / "Pictures" / "DannyCapture")
            },
            "hotkeys": {
                "simple_capture": "<ctrl>+<shift>+e",
                "fullscreen_capture": "<ctrl>+<alt>+f",
                "window_capture": "<ctrl>+<alt>+w",
                "region_capture": "<ctrl>+<alt>+u",
                "size_capture": "<ctrl>+<alt>+s",
                "repeat_capture": "<ctrl>+<alt>+r"
            },
            "appearance": {
                "theme": "dark",
                "language": "ko",
                "corner_roundness": 8
            },
            "system": {
                "startup": False,
                "check_updates": True
            }
        }
        self.config = {}
        self.load()

    def load(self):
        self.app_dir.mkdir(parents=True, exist_ok=True)
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    self.config = self._merge_dicts(self.default_config, loaded)
            except Exception as e:
                print(f"Failed to load config: {e}")
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            
        self.save()

    def save(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def get(self, section, key=None):
        if key is None:
            return self.config.get(section, {})
        return self.config.get(section, {}).get(key)

    def set(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()
        
        if section == "system" and key == "startup":
            self.update_startup_registry(value)

    def update_startup_registry(self, enabled):
        import platform
        if platform.system() != "Windows":
            return
            
        import winreg
        import sys
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "DannyCapture"
        
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            import os
            exe_path = os.path.abspath(sys.argv[0])
            
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to update startup registry: {e}")

    def _merge_dicts(self, default, custom):
        result = default.copy()
        for k, v in custom.items():
            if isinstance(v, dict) and k in result and isinstance(result[k], dict):
                result[k] = self._merge_dicts(result[k], v)
            else:
                result[k] = v
        return result
