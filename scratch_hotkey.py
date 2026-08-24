import sys
import ctypes
from ctypes import wintypes
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication

class HotkeyFilter(QAbstractNativeEventFilter):
    def nativeEvent(self, eventType, message):
        try:
            msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
            if msg.message == 0x0312: # WM_HOTKEY
                print(f"Hotkey pressed: {msg.wParam}", flush=True)
                if msg.wParam == 1:
                    print("Exiting...")
                    QApplication.quit()
                return True, 0
        except Exception as e:
            print("Error:", e)
        return False, 0

app = QApplication(sys.argv)
filter = HotkeyFilter()
app.installNativeEventFilter(filter)

user32 = ctypes.windll.user32
# Register Ctrl+Alt+D (Ctrl=2, Alt=1 -> 3)
# ID = 1, MOD_CONTROL | MOD_ALT = 3, 'D' = 0x44
user32.RegisterHotKey(None, 1, 3, 0x44)

print("Press Ctrl+Alt+D to exit.", flush=True)

# Also test another one
user32.RegisterHotKey(None, 2, 3, 0x46) # Ctrl+Alt+F

# Call processEvents periodically or just wait
app.exec()

user32.UnregisterHotKey(None, 1)
user32.UnregisterHotKey(None, 2)
