# 오버레이를 반복 생성해도 GDI 객체·시스템 메모리가 쌓이지 않아야 한다 (캡처당 mss 핸들 누수 회귀 테스트)
import sys, os, ctypes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psutil
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)
from ui.overlay import CaptureOverlay

h = ctypes.windll.kernel32.OpenProcess(0x0400, False, os.getpid())
gdi = lambda: ctypes.windll.user32.GetGuiResources(h, 0)
import subprocess
def used():  # paged pool: where leaked GDI bitmaps live (system-wide RAM 'used' is too noisy)
    out = subprocess.run(["typeperf", r"\Memory\Pool Paged Bytes", "-sc", "1"], capture_output=True, text=True, encoding="cp949", errors="replace").stdout
    vals = [l.split(",")[-1].strip().strip('"') for l in out.splitlines() if l.startswith('"') and "Pool" not in l]
    return int(float(vals[-1])) // (1024 * 1024)

CaptureOverlay()  # 1회 워밍업 (폰트·Qt 내부 캐시)
g0, m0 = gdi(), used()
for _ in range(30):
    CaptureOverlay()
dg, dm = gdi() - g0, used() - m0
print(f"30 overlays: GDI +{dg}, paged pool +{dm}MB")
ok = dg <= 3 and dm < 100
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
