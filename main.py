import sys
from pathlib import Path
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from utils.logger import setup_logger
from utils.config import ConfigManager

def acquire_single_instance():
    """Returns True if this is the only running instance (named mutex)."""
    import ctypes
    # use_last_error + get_last_error: ctypes internals may clobber the thread's
    # last-error between calls, so GetLastError() cannot be called directly.
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    # Handle kept open for process lifetime; released automatically on exit
    acquire_single_instance._handle = kernel32.CreateMutexW(None, False, "DannyCapture_SingleInstance")
    return ctypes.get_last_error() != 183  # ERROR_ALREADY_EXISTS

def main():
    if not acquire_single_instance():
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            None,
            "Danny Capture 가 이미 실행 중입니다.\n트레이 아이콘을 확인하세요.",
            "Danny Capture", 0x40)  # MB_ICONINFORMATION
        return

    # Setup logger and config
    setup_logger()
    config = ConfigManager()
    
    # Allow Ctrl+C to kill the application from the terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Enable High DPI scaling
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        pass
        
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    
    icon_path = Path(__file__).parent / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        
    # Instantiate UI
    from ui.tray import TrayIcon
    from ui.main_toolbar import MainToolbar
    
    app.main_toolbar = MainToolbar()
    app.tray_icon = TrayIcon(app_instance=app)
    app.tray_icon.show()
    
    # Setup Hotkeys
    from core.hotkey_manager import HotkeyManager
    app.hotkey_manager = HotkeyManager()
    app.hotkey_manager.sig_simple_capture.connect(app.main_toolbar.start_simple_capture)
    app.hotkey_manager.sig_full_capture.connect(app.main_toolbar.start_full_capture)
    app.hotkey_manager.sig_window_capture.connect(app.main_toolbar.start_window_capture)
    app.hotkey_manager.sig_region_capture.connect(app.main_toolbar.start_simple_capture)
    app.hotkey_manager.sig_size_capture.connect(app.main_toolbar.start_size_capture)
    app.hotkey_manager.sig_repeat_capture.connect(app.main_toolbar.start_repeat_capture)
    app.aboutToQuit.connect(app.hotkey_manager.stop)

    # Warn about hotkeys another program already owns
    if app.hotkey_manager.failed_hotkeys:
        from PySide6.QtWidgets import QSystemTrayIcon
        app.tray_icon.showMessage(
            "단축키 등록 실패",
            "다른 프로그램이 사용 중입니다:\n" + ", ".join(app.hotkey_manager.failed_hotkeys)
            + "\n환경설정에서 단축키를 변경하세요.",
            QSystemTrayIcon.Warning)
    
    # Toolbar starts hidden — capture via hotkey only, editor appears after capture
    
    app.setQuitOnLastWindowClosed(False) # Keep running in tray
    
    print("Danny Capture started...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
