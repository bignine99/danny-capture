"""진단 v2: 실제 캡처 경로를 끝까지 태워 최종 이미지를 저장한다."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from core.hotkey_manager import HotkeyManager
from core.capture import CaptureEngine
from ui.overlay import CaptureOverlay

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diag_shots2")
os.makedirs(OUT, exist_ok=True)

RECT = (1920, 0, 1920, 1080)   # 가운데 모니터 = Chrome 이 있는 화면

def save(img, name):
    img.save(os.path.join(OUT, f"{name}.png"))
    s = img.copy(); s.thumbnail((1000, 1000))
    s.save(os.path.join(OUT, f"{name}_small.png"))
    print(f"saved {name} {img.size}", flush=True)

app = QApplication(sys.argv)
eng = CaptureEngine()

def on_hotkey():
    print(">>> HOTKEY", flush=True)
    ov = CaptureOverlay(mode="region")   # 여기서 화면 동결
    ov.on_capture = None
    ov.show()
    QTimer.singleShot(300, lambda: (ov.activateWindow(), ov.raise_()))  # 사용자가 클릭한 것과 같은 효과
    QTimer.singleShot(900, lambda: finish(ov))

def finish(ov):
    x, y, w, h = RECT
    save(eng.crop_frozen(ov.frozen_image, ov.frozen_origin, x, y, w, h), "FINAL_from_frozen")
    save(eng.capture_region(x, y, w, h), "FINAL_from_live")
    ov.close()
    print(">>> DONE", flush=True)

hm = HotkeyManager()
hm.sig_simple_capture.connect(on_hotkey)
print("대기 중... 드롭다운 띄우고 Ctrl+Shift+E", flush=True)
sys.exit(app.exec())
