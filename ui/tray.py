from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction
import sys

class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None, app_instance=None):
        super().__init__(parent)
        self.app_instance = app_instance
        
        # Use actual app icon
        from pathlib import Path
        icon_path = Path(__file__).parent.parent / "icon.ico"
        if icon_path.exists():
            self.setIcon(QIcon(str(icon_path)))
        else:
            from PySide6.QtWidgets import QStyle
            self.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.setToolTip("Danny Capture")
        
        self.menu = QMenu()
        
        from utils.config import ConfigManager
        config = ConfigManager().get("hotkeys")
        
        # Actions
        self.action_simple = QAction(f"간편 캡쳐 ({config.get('simple_capture', '<ctrl>+<alt>+d')})", self)
        self.action_full = QAction(f"전체화면 캡쳐 ({config.get('fullscreen_capture', '<ctrl>+<alt>+f')})", self)
        self.action_window = QAction(f"창 캡쳐 ({config.get('window_capture', '<ctrl>+<alt>+w')})", self)
        self.action_region = QAction(f"단위영역 캡쳐 ({config.get('region_capture', '<ctrl>+<alt>+u')})", self)
        self.action_size = QAction(f"크기지정 캡쳐 ({config.get('size_capture', '<ctrl>+<alt>+s')})", self)
        self.action_repeat = QAction(f"마지막 영역 재캡처 ({config.get('repeat_capture', '<ctrl>+<alt>+r')})", self)
        
        self.action_settings = QAction("환경설정", self)
        self.action_exit = QAction("종료", self)
        
        # Connect signals
        self.action_exit.triggered.connect(self.quit_app)
        self.action_settings.triggered.connect(self.show_settings)
        
        # Connect capture signals
        if hasattr(self.app_instance, 'main_toolbar'):
            self.action_simple.triggered.connect(self.app_instance.main_toolbar.start_simple_capture)
            self.action_full.triggered.connect(self.app_instance.main_toolbar.start_full_capture)
            self.action_window.triggered.connect(self.app_instance.main_toolbar.start_window_capture)
            self.action_region.triggered.connect(self.app_instance.main_toolbar.start_simple_capture)
            self.action_size.triggered.connect(self.app_instance.main_toolbar.start_size_capture)
            self.action_repeat.triggered.connect(self.app_instance.main_toolbar.start_repeat_capture)
        
        # Add actions to menu
        self.menu.addAction(self.action_simple)
        self.menu.addAction(self.action_full)
        self.menu.addAction(self.action_window)
        self.menu.addAction(self.action_region)
        self.menu.addAction(self.action_size)
        self.menu.addAction(self.action_repeat)
        self.menu.addSeparator()
        self.menu.addAction(self.action_settings)
        self.menu.addAction(self.action_exit)
        
        self.setContextMenu(self.menu)
        self.activated.connect(self.on_activated)

    def refresh_labels(self):
        """Re-read hotkeys from config so menu labels follow settings changes."""
        from utils.config import ConfigManager
        config = ConfigManager().get("hotkeys")
        self.action_simple.setText(f"간편 캡쳐 ({config.get('simple_capture', '<ctrl>+<alt>+d')})")
        self.action_full.setText(f"전체화면 캡쳐 ({config.get('fullscreen_capture', '<ctrl>+<alt>+f')})")
        self.action_window.setText(f"창 캡쳐 ({config.get('window_capture', '<ctrl>+<alt>+w')})")
        self.action_region.setText(f"단위영역 캡쳐 ({config.get('region_capture', '<ctrl>+<alt>+u')})")
        self.action_size.setText(f"크기지정 캡쳐 ({config.get('size_capture', '<ctrl>+<alt>+s')})")
        self.action_repeat.setText(f"마지막 영역 재캡처 ({config.get('repeat_capture', '<ctrl>+<alt>+r')})")

    def on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            # Show main toolbar
            if hasattr(self.app_instance, 'main_toolbar'):
                self.app_instance.main_toolbar.show_normal()

    def show_settings(self):
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog()
        dialog.exec()

    def quit_app(self):
        QApplication.quit()
