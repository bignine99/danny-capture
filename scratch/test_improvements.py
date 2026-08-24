# -*- coding: utf-8 -*-
"""5개 개선 항목 검증 하네스. 임시 APPDATA 에서 돌아 실사용 config 를 건드리지 않는다."""
import os, sys, io, tempfile, subprocess, json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP_APPDATA = tempfile.mkdtemp(prefix="dc_test_appdata_")
os.environ["APPDATA"] = TMP_APPDATA          # utils.config 임포트 전에 설정
TMP_SAVE = Path(tempfile.mkdtemp(prefix="dc_test_save_"))

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}", flush=True)

# ============ 1. config: 이식 가능 기본값 + 강제 덮어쓰기 제거 (별도 프로세스 2회) ============
env = {**os.environ, "APPDATA": TMP_APPDATA, "PYTHONIOENCODING": "utf-8"}
code1 = (
    "import sys; sys.path.insert(0, r'%s')\n"
    "from utils.config import ConfigManager\n"
    "c = ConfigManager()\n"
    "print(c.get('paths','save_directory'))\n"
    "print(c.get('capture','auto_save'))\n"
    "print(c.get('hotkeys','repeat_capture'))\n"
    "print(c.get('hotkeys','scroll_capture'))\n"
    "c.set('paths','save_directory', r'%s')\n"
) % (ROOT, TMP_SAVE)
out1 = subprocess.run([sys.executable, "-c", code1], env=env, capture_output=True, text=True).stdout.strip().splitlines()
check("1a 기본 저장 경로가 이식 가능(Pictures)", out1 and "Pictures" in out1[0], out1[0] if out1 else "no output")
check("1b auto_save 기본 True", len(out1) > 1 and out1[1] == "True")
check("1c repeat_capture 기본키 존재", len(out1) > 2 and out1[2] == "<ctrl>+<alt>+r")
check("1d scroll_capture 죽은 키 제거", len(out1) > 3 and out1[3] == "None")

code2 = (
    "import sys; sys.path.insert(0, r'%s')\n"
    "from utils.config import ConfigManager\n"
    "print(ConfigManager().get('paths','save_directory'))\n"
) % ROOT
out2 = subprocess.run([sys.executable, "-c", code2], env=env, capture_output=True, text=True).stdout.strip()
check("1e 재실행 후 사용자 경로 유지(강제 덮어쓰기 제거)", out2 == str(TMP_SAVE), out2)

# ============ 이하 동일 프로세스: Qt 필요 ============
from utils.config import ConfigManager
cfg = ConfigManager()
cfg.set("paths", "save_directory", str(TMP_SAVE))

# ============ 2. 단일 인스턴스 뮤텍스 ============
import main as main_mod
first = main_mod.acquire_single_instance()
second = main_mod.acquire_single_instance()
check("2a 첫 획득 성공", first is True)
check("2b 두 번째 획득 거부", second is False)

# ============ 3. 단축키 등록 실패 추적 ============
import ctypes
user32 = ctypes.windll.user32
# ctrl+shift+e (MOD_CONTROL|MOD_SHIFT=0x0006, 'e'=0x45) 를 먼저 선점
pre = user32.RegisterHotKey(None, 999, 0x0006, 0x45)
from core.hotkey_manager import HotkeyManager
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)
hm = HotkeyManager()
check("3a 선점된 단축키가 failed_hotkeys 에 잡힘",
      pre and any("<ctrl>+<shift>+e" in f for f in hm.failed_hotkeys), str(hm.failed_hotkeys))
check("3b 나머지 단축키는 등록 성공", len(hm._registered_ids) >= 4, f"{len(hm._registered_ids)} registered")
check("3c 재캡처 시그널 존재", hasattr(hm, "sig_repeat_capture"))
hm.stop(); user32.UnregisterHotKey(None, 999)

# ============ 4. 저장 흐름 ============
from PIL import Image
from ui.main_toolbar import MainToolbar

tb = MainToolbar()
msgs = []
tb.notifier.show_message = lambda t, m: msgs.append((t, m))
tb.notifier.show_capture_success = lambda *a, **k: msgs.append(("success", a))

img = Image.new("RGB", (80, 60), "blue")

# 4a auto_save on → 파일 생성 + 편집기에 경로 전달
cfg.set("capture", "auto_save", True)
before = set(TMP_SAVE.iterdir())
tb._handle_capture_result(img)
new_files = set(TMP_SAVE.iterdir()) - before
check("4a auto_save=True: 파일 생성", len(new_files) == 1, str(new_files))
check("4b 편집기에 원본 경로 전달(덮어쓰기 저장용)",
      tb.editor.source_filepath is not None and Path(tb.editor.source_filepath) in new_files)
tb.editor.close()

# 4c auto_save off → 파일 없음, 클립보드 알림
cfg.set("capture", "auto_save", False)
msgs.clear()
before = set(TMP_SAVE.iterdir())
tb._handle_capture_result(img)
check("4c auto_save=False: 파일 미생성", set(TMP_SAVE.iterdir()) == before)
check("4d 클립보드 완료 알림", any("클립보드" in str(m) for m in msgs), str(msgs))
check("4e 편집기 source_filepath=None", tb.editor.source_filepath is None)
tb.editor.close()

# 4f 저장 실패 → 예외 전파 없이 알림 + 편집기는 뜸
cfg.set("capture", "auto_save", True)
cfg.set("paths", "save_directory", r"Q:\definitely\does\not\exist")
msgs.clear()
try:
    tb._handle_capture_result(img)
    survived = True
except Exception as e:
    survived = False
check("4f 저장 실패에도 생존", survived)
check("4g 실패 알림 발송", any("저장 실패" in str(m) for m in msgs), str(msgs))
check("4h 실패해도 편집기 표시(캡처 유실 방지)", tb.editor is not None and tb.editor.source_filepath is None)
tb.editor.close()
cfg.set("paths", "save_directory", str(TMP_SAVE))

# ============ 5. Crop ============
from ui.editor import EditorWindow
from PySide6.QtCore import QRectF, QRect, QTimer, QEventLoop

ed = EditorWindow(Image.new("RGB", (200, 150), "white"))
check("5a scene.on_crop 연결", ed.scene.on_crop == ed.apply_crop)
check("5b 자르기 버튼 존재", hasattr(ed, "btn_crop"))
ed.apply_crop(QRectF(20, 10, 100, 80))
sr = ed.scene.sceneRect()
check("5c 크롭 후 sceneRect 100x80", sr.width() == 100 and sr.height() == 80, f"{sr.width()}x{sr.height()}")
ed.apply_crop(QRectF(0, 0, 2, 2))   # 너무 작은 선택은 무시
sr = ed.scene.sceneRect()
check("5d 5px 미만 선택 무시", sr.width() == 100 and sr.height() == 80)
ed.apply_crop(QRectF(-50, -50, 500, 500))  # 범위 밖은 클램프
sr = ed.scene.sceneRect()
check("5e 범위 밖 클램프", sr.width() == 100 and sr.height() == 80, f"{sr.width()}x{sr.height()}")
ed.close()

# ============ 6. 마지막 영역 재캡처 ============
# 6a _on_region_captured 가 last_region 을 기록
class FakeOverlay:
    pass
tb.overlay = FakeOverlay()
from core.capture import CaptureEngine
tb.overlay.frozen_image, tb.overlay.frozen_origin = CaptureEngine().freeze_screen()
captured = []
orig_handle = tb._handle_capture_result
tb._handle_capture_result = lambda im: captured.append(im)
tb._on_region_captured(QRect(10, 20, 60, 40))
check("6a last_region 기록", cfg.get("capture", "last_region") == [10, 20, 60, 40],
      str(cfg.get("capture", "last_region")))
check("6b 크롭 결과 60x40", captured and captured[0].size == (60, 40))

# 6c start_repeat_capture → 100ms 후 라이브 캡처
captured.clear()
tb.start_repeat_capture()
loop = QEventLoop(); QTimer.singleShot(500, loop.quit); loop.exec()
check("6c 재캡처 결과 60x40", captured and captured[0].size == (60, 40),
      str(captured[0].size) if captured else "none")

# 6d 저장된 영역 없음 → 알림만
msgs.clear()
cfg.config["capture"].pop("last_region", None); cfg.save()
tb._handle_capture_result = orig_handle
tb.start_repeat_capture()
check("6d 영역 없으면 안내 알림", any("재캡처 불가" in str(m) for m in msgs), str(msgs))

# ============ 7. 리뷰 지적 수정 검증 ============
import shiboken6

# R1 같은 단축키 문자열 2회 → 중복으로 보고 (dict 충돌로 사라지지 않음)
cfg.set("hotkeys", "size_capture", "<ctrl>+<alt>+s")
cfg.set("hotkeys", "repeat_capture", "<ctrl>+<alt>+s")
hm2 = HotkeyManager(); hm2.start()
check("R1 중복 단축키 감지", any("중복" in f for f in hm2.failed_hotkeys), str(hm2.failed_hotkeys))
hm2.stop()

# R2 오타 토큰 → 무효 처리 (잘못된 전역 Ctrl+R 이 등록되지 않아야 함)
cfg.set("hotkeys", "repeat_capture", "<ctrl>+<ait>+r")   # alt 오타
hm3 = HotkeyManager(); hm3.start()
check("R2a 오타 조합 '인식 불가' 보고", any("인식할 수 없는" in f for f in hm3.failed_hotkeys), str(hm3.failed_hotkeys))
free = user32.RegisterHotKey(None, 998, 0x0002, 0x52)    # Ctrl+R 이 비어 있으면 성공
check("R2b 전역 Ctrl+R 을 가로채지 않음", bool(free))
if free: user32.UnregisterHotKey(None, 998)
hm3.stop()
cfg.set("hotkeys", "repeat_capture", "<ctrl>+<alt>+r")

# R3 연속 캡처에도 이전 편집기 생존
cfg.set("capture", "auto_save", False)
tb._handle_capture_result(img)
ed1 = tb.editor
tb._handle_capture_result(img)
ed2 = tb.editor
check("R3a 편집기 2개 모두 목록에 유지", len(tb.editors) >= 2, f"{len(tb.editors)} editors")
check("R3b 이전 편집기 위젯 생존", shiboken6.isValid(ed1) and ed1 is not ed2)
ed1.close(); ed2.close()

# R4 자동 저장 실패 시에도 편집기 저장 다이얼로그가 죽지 않음
cfg.set("paths", "save_directory", r"Q:\definitely\does\not\exist")
from PySide6.QtWidgets import QFileDialog
orig_dlg = QFileDialog.getSaveFileName
QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: ("", ""))
ed3 = EditorWindow(Image.new("RGB", (50, 50), "red"), source_filepath=None)
try:
    ed3.save_image(); rescued = True
except Exception:
    rescued = False
QFileDialog.getSaveFileName = orig_dlg
check("R4 무효 저장폴더에서도 저장 경로 산출 생존", rescued)
ed3.close()
cfg.set("paths", "save_directory", str(TMP_SAVE))

# R5 화면 밖 last_region → 검은 이미지 대신 안내
cfg.set("capture", "last_region", [99999, 99999, 100, 100])
msgs.clear()
captured2 = []
orig2 = tb._handle_capture_result
tb._handle_capture_result = lambda im: captured2.append(im)
tb.start_repeat_capture()
loop = QEventLoop(); QTimer.singleShot(400, loop.quit); loop.exec()
tb._handle_capture_result = orig2
check("R5a 화면 밖 영역 캡처 차단", not captured2)
check("R5b 화면 밖 안내 알림", any("화면 밖" in str(m) for m in msgs), str(msgs))

# R6 자르기 버튼 재클릭에도 체크·모드 유지 (파괴적 크롭 오동작 방지)
ed4 = EditorWindow(Image.new("RGB", (50, 50), "white"))
ed4.btn_crop.click(); ed4.btn_crop.click()
check("R6 재클릭 후에도 crop 버튼 체크 유지", ed4.btn_crop.isChecked() and ed4.scene.mode == "crop")
ed4.close()

# R7 트레이 라벨 갱신
from ui.tray import TrayIcon
tray = TrayIcon(app_instance=None)
cfg.set("hotkeys", "repeat_capture", "<ctrl>+<alt>+9")
tray.refresh_labels()
check("R7 트레이 라벨이 새 단축키 반영", "<ctrl>+<alt>+9" in tray.action_repeat.text(), tray.action_repeat.text())
cfg.set("hotkeys", "repeat_capture", "<ctrl>+<alt>+r")

# ============ 결과 ============
fails = [r for r in results if not r[1]]
print(f"\n===== {len(results) - len(fails)}/{len(results)} PASS =====")
sys.exit(1 if fails else 0)
