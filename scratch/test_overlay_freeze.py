# -*- coding: utf-8 -*-
"""오버레이가 라이브 화면 대신 '동결 화면'을 보여주는지 실측한다."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mss
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QEventLoop, QTimer, QPoint

app = QApplication(sys.argv)

def settle(ms=600):
    loop = QEventLoop(); QTimer.singleShot(ms, loop.quit); loop.exec()

X, Y, W, H = 400, 300, 200, 200
w = QWidget()
w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
w.setGeometry(X, Y, W, H)
w.setStyleSheet("background-color: rgb(0,0,255);")   # 파랑 = "드롭다운 열림"
w.show(); settle()

from ui.overlay import CaptureOverlay
ov = CaptureOverlay(mode="region")                    # 여기서 파란 화면이 동결됨

w.setStyleSheet("background-color: rgb(0,255,0);")    # 초록 = "드롭다운 닫힘"
w.repaint(); settle(300)

ov.show(); ov.raise_(); settle(800)                   # 오버레이 표시 (동결 배경 + 어둡게)

sct = mss.mss()
def px(x, y):
    im = sct.grab({"left": x, "top": y, "width": 1, "height": 1})
    b, g, r = im.raw[0], im.raw[1], im.raw[2]
    return (r, g, b)

cx, cy = X + W // 2, Y + H // 2
p1 = px(cx, cy)
# 어둡게(알파120) 깔린 동결-파랑: B ≈ 255*(135/255) ≈ 135, G ≈ 0 이어야 한다.
# 라이브가 비치면 G 가 높게 나온다.
ok_frozen = p1[2] > 90 and p1[1] < 60
print(f"1 오버레이 표시 중 픽셀: {p1}  (기대: 어두운 파랑 / 라이브면 초록)")
print(f"PASS 오버레이가 동결 화면을 보여줌: {ok_frozen}")

# 선택 영역을 테스트 창 위에 걸치고 다시 그리기 → 원래 밝기의 동결-파랑(≈255)
ov.start_pos = QPoint(X, Y)
ov.current_pos = QPoint(X + W, Y + H)
ov.repaint(); settle(400)
p2 = px(cx, cy)
ok_reveal = p2[2] > 200 and p2[1] < 60
print(f"2 선택 영역 내부 픽셀: {p2}  (기대: 밝은 파랑 255 부근)")
print(f"PASS 선택 영역은 원래 밝기로 드러남: {ok_reveal}")

# 최종 크롭도 여전히 동결본(파랑)에서 나오는지
from core.capture import CaptureEngine
crop = CaptureEngine().crop_frozen(ov.frozen_image, ov.frozen_origin, X, Y, W, H)
p3 = crop.getpixel((W // 2, H // 2))
ok_crop = p3[2] > 200 and p3[1] < 60
print(f"3 최종 크롭 픽셀: {p3}")
print(f"PASS 크롭 결과 = 화면에 보인 것: {ok_crop}")

ov.close(); w.close()
print("\nALL PASS" if (ok_frozen and ok_reveal and ok_crop) else "\nFAIL")
sys.exit(0 if (ok_frozen and ok_reveal and ok_crop) else 1)
