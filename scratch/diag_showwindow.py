"""가설 검증: 프로세스 시작 방식(SW_HIDE)이 첫 창의 표시를 막는가?"""
import sys, os, ctypes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.editor import EditorWindow

app = QApplication(sys.argv)
w = EditorWindow(Image.new("RGB", (300, 200), "white"))
w.show()

def check():
    hwnd = int(w.winId())
    visible = bool(ctypes.windll.user32.IsWindowVisible(hwnd))
    print(f"RESULT visible={visible}", flush=True)
    app.quit()

QTimer.singleShot(1200, check)
app.exec()
