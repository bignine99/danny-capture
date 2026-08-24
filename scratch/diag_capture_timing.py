"""진단 전용: 드롭다운이 어느 시점에 사라지는지 실측한다. 앱 코드는 건드리지 않는다."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mss
from PIL import Image
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from core.hotkey_manager import HotkeyManager
from ui.overlay import CaptureOverlay

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diag_shots")
os.makedirs(OUT, exist_ok=True)

_sct = mss.mss()

def grab():
    mon = _sct.monitors[0]
    im = _sct.grab(mon)
    return Image.frombytes("RGB", im.size, im.bgra, "raw", "BGRX")

def save(img, name):
    full = os.path.join(OUT, f"{name}.png")
    img.save(full)
    small = img.copy()
    small.thumbnail((1100, 1100))
    small.save(os.path.join(OUT, f"{name}_small.png"))
    print(f"saved {name}  {img.size}", flush=True)

app = QApplication(sys.argv)

def on_hotkey():
    print(">>> HOTKEY fired", flush=True)
    save(grab(), "A_at_hotkey_instant")          # 단축키가 들어온 바로 그 순간
    QTimer.singleShot(100, step2)

def step2():
    ov = CaptureOverlay(mode="region")            # 현재 앱이 화면을 얼리는 지점
    save(ov.frozen_image, "B_overlay_constructed")
    ov.show()
    QTimer.singleShot(250, lambda: step3(ov))

def step3(ov):
    save(grab(), "C_after_overlay_shown")         # 오버레이가 뜬 뒤
    ov.close()
    print(">>> DONE - 3장 저장 완료", flush=True)

hm = HotkeyManager()
hm.sig_simple_capture.connect(on_hotkey)
print("진단 대기 중... Chrome 주소창 드롭다운을 띄우고 Ctrl+Shift+E 를 누르세요.", flush=True)
sys.exit(app.exec())
