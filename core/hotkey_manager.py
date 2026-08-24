import sys
import ctypes
from ctypes import wintypes
from PySide6.QtCore import QObject, Signal, QAbstractNativeEventFilter, QCoreApplication
from utils.config import ConfigManager

user32 = ctypes.windll.user32

WM_HOTKEY = 0x0312

VK_MAP = {
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46,
    'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C,
    'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52,
    's': 0x53, 't': 0x54, 'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58,
    'y': 0x59, 'z': 0x5A,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74, 'f6': 0x75,
    'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
    'space': 0x20, 'enter': 0x0D, 'esc': 0x1B, 'tab': 0x09, 'backspace': 0x08,
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    'print_screen': 0x2C, 'prtscr': 0x2C, 'insert': 0x2D, 'delete': 0x2E,
    'home': 0x24, 'end': 0x23, 'page_up': 0x21, 'page_down': 0x22
}
MOD_MAP = {
    'ctrl': 0x0002,
    'control': 0x0002,
    'alt': 0x0001,
    'shift': 0x0004,
    'win': 0x0008,
    'windows': 0x0008
}

class Win32HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def nativeEventFilter(self, eventType, message):
        try:
            msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
            if msg.message == WM_HOTKEY:
                self.manager._handle_hotkey(msg.wParam)
                return True, 0
        except Exception:
            pass
        return False, 0

class HotkeyManager(QObject):
    sig_simple_capture = Signal()
    sig_full_capture = Signal()
    sig_window_capture = Signal()
    sig_region_capture = Signal()
    sig_size_capture = Signal()
    sig_repeat_capture = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self._callbacks = {}
        self._filter = None
        self._next_id = 1
        self._registered_ids = []
        self.failed_hotkeys = []
        self.start()

    def _on_activate_simple(self):
        import sys
        print("HOTKEY: Simple capture triggered", flush=True)
        self.sig_simple_capture.emit()

    def _on_activate_full(self):
        self.sig_full_capture.emit()

    def _on_activate_window(self):
        self.sig_window_capture.emit()

    def _on_activate_region(self):
        self.sig_region_capture.emit()

    def _on_activate_size(self):
        self.sig_size_capture.emit()

    def _on_activate_repeat(self):
        self.sig_repeat_capture.emit()
        
    def _parse_hotkey(self, hk_str):
        """Returns (mod, vk, valid). An unknown token (typo) invalidates the whole
        combo instead of being silently dropped — otherwise 'ctrl+ait+r' would
        register a global Ctrl+R and hijack every app's shortcut."""
        parts = hk_str.lower().replace('<', '').replace('>', '').split('+')
        mod = 0
        vk = 0
        valid = True
        for p in parts:
            p = p.strip()
            if p in MOD_MAP:
                mod |= MOD_MAP[p]
            elif p in VK_MAP:
                if vk:
                    valid = False  # two key tokens in one combo
                vk = VK_MAP[p]
            elif p:
                valid = False  # unrecognized token
        if vk == 0:
            valid = False
        return mod, vk, valid

    def _handle_hotkey(self, hotkey_id):
        if hotkey_id in self._callbacks:
            self._callbacks[hotkey_id]()

    def start(self):
        self.stop()
        
        if self._filter is None:
            self._filter = Win32HotkeyFilter(self)
            app = QCoreApplication.instance()
            if app:
                app.installNativeEventFilter(self._filter)
        
        hotkeys = self.config.get("hotkeys")

        # List (not dict): two actions configured with the same string must be
        # detected as duplicates, not silently collapsed by dict keys.
        entries = [
            ("간편 캡쳐", hotkeys.get('simple_capture', '<ctrl>+<alt>+d'), self._on_activate_simple),
            ("전체화면 캡쳐", hotkeys.get('fullscreen_capture', '<ctrl>+<alt>+f'), self._on_activate_full),
            ("창 캡쳐", hotkeys.get('window_capture', '<ctrl>+<alt>+w'), self._on_activate_window),
            ("단위영역 캡쳐", hotkeys.get('region_capture', '<ctrl>+<alt>+u'), self._on_activate_region),
            ("크기지정 캡쳐", hotkeys.get('size_capture', '<ctrl>+<alt>+s'), self._on_activate_size),
            ("마지막 영역 재캡처", hotkeys.get('repeat_capture', '<ctrl>+<alt>+r'), self._on_activate_repeat),
        ]

        self.failed_hotkeys = []
        seen = {}
        try:
            for label, hk, cb in entries:
                mod, vk, valid = self._parse_hotkey(hk)
                if not valid:
                    self.failed_hotkeys.append(f"{label}: {hk} (인식할 수 없는 조합)")
                    continue
                if (mod, vk) in seen:
                    self.failed_hotkeys.append(f"{label}: {hk} ('{seen[(mod, vk)]}' 와 중복)")
                    continue
                seen[(mod, vk)] = label
                hk_id = self._next_id
                self._next_id += 1
                # 0x4000 is MOD_NOREPEAT, prevents repeated trigger when holding down
                success = user32.RegisterHotKey(None, hk_id, mod | 0x4000, vk)
                if not success:
                    # try without MOD_NOREPEAT for compatibility
                    success = user32.RegisterHotKey(None, hk_id, mod, vk)
                if success:
                    self._callbacks[hk_id] = cb
                    self._registered_ids.append(hk_id)
                else:
                    self.failed_hotkeys.append(f"{label}: {hk} (다른 프로그램이 사용 중)")
            if self.failed_hotkeys:
                print(f"Hotkey registration failed for: {self.failed_hotkeys}", flush=True)
            else:
                print("Hotkeys registered successfully via Windows API.", flush=True)
        except Exception as e:
            print(f"Failed to register hotkeys: {e}", flush=True)

    def stop(self):
        try:
            for hk_id in self._registered_ids:
                user32.UnregisterHotKey(None, hk_id)
            self._registered_ids.clear()
            self._callbacks.clear()
        except:
            pass
