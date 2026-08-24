from PySide6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, QCheckBox, QComboBox, QSpinBox, QPushButton, QHBoxLayout, QLineEdit, QFileDialog
from utils.config import ConfigManager
from utils.config import ConfigManager

def apply_mica(hwnd):
    import ctypes
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(int(hwnd), 20, ctypes.byref(ctypes.c_int(1)), 4) # Dark mode
        ctypes.windll.dwmapi.DwmSetWindowAttribute(int(hwnd), 38, ctypes.byref(ctypes.c_int(2)), 4) # Mica
    except Exception:
        pass

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("환경설정 - Danny Capture")
        self.resize(400, 300)
        self.config = ConfigManager()
        
        apply_mica(int(self.winId()))
        self.setStyleSheet("""
            QDialog {
                background-color: transparent;
            }
            QLabel, QCheckBox {
                color: white;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: rgba(255, 255, 255, 0.05);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 5px;
                padding: 4px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border-radius: 5px;
                padding: 6px 12px;
                border: 1px solid transparent;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 5px;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: rgba(255, 255, 255, 0.05);
                color: white;
                padding: 6px 12px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # Tab 1: Capture
        self.tab_capture = QWidget()
        capture_layout = QFormLayout(self.tab_capture)
        
        self.chk_auto_copy = QCheckBox("캡처 후 클립보드에 자동 복사")
        self.chk_auto_save = QCheckBox("캡처 후 파일로 자동 저장")
        self.chk_show_editor = QCheckBox("캡처 후 편집기 표시")
        self.chk_startup = QCheckBox("Windows 시작 시 자동 실행")
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(0, 10)
        self.spin_delay.setSuffix(" 초")
        self.combo_format = QComboBox()
        self.combo_format.addItems(["PNG", "JPEG", "BMP"])
        
        capture_layout.addRow("클립보드:", self.chk_auto_copy)
        capture_layout.addRow("자동 저장:", self.chk_auto_save)
        capture_layout.addRow("편집기:", self.chk_show_editor)
        capture_layout.addRow("부팅 설정:", self.chk_startup)
        capture_layout.addRow("캡처 지연:", self.spin_delay)
        capture_layout.addRow("저장 포맷:", self.combo_format)
        
        self.path_layout = QHBoxLayout()
        self.edit_save_dir = QLineEdit()
        self.btn_browse = QPushButton("찾아보기...")
        self.btn_browse.clicked.connect(self.browse_directory)
        self.path_layout.addWidget(self.edit_save_dir)
        self.path_layout.addWidget(self.btn_browse)
        capture_layout.addRow("저장 폴더:", self.path_layout)
        
        self.tabs.addTab(self.tab_capture, "캡처 설정")
        
        # Tab 2: Hotkeys
        self.tab_hotkeys = QWidget()
        hotkey_layout = QFormLayout(self.tab_hotkeys)
        self.hk_simple = QLineEdit()
        self.hk_full = QLineEdit()
        self.hk_window = QLineEdit()
        self.hk_region = QLineEdit()
        self.hk_size = QLineEdit()
        self.hk_repeat = QLineEdit()
        
        hotkey_layout.addRow("간편 캡쳐:", self.hk_simple)
        hotkey_layout.addRow("전체화면 캡쳐:", self.hk_full)
        hotkey_layout.addRow("창 캡쳐:", self.hk_window)
        hotkey_layout.addRow("단위영역 캡쳐:", self.hk_region)
        hotkey_layout.addRow("크기지정 캡쳐:", self.hk_size)
        hotkey_layout.addRow("마지막 영역 재캡처:", self.hk_repeat)
        
        self.tabs.addTab(self.tab_hotkeys, "단축키 설정")
        
        # Add tabs
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("확인")
        self.btn_cancel = QPushButton("취소")
        
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)

    def browse_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "저장 폴더 선택", self.edit_save_dir.text())
        if dir_path:
            self.edit_save_dir.setText(dir_path)

    def load_settings(self):
        self.chk_auto_copy.setChecked(self.config.get("capture", "auto_copy_clipboard"))
        self.chk_auto_save.setChecked(bool(self.config.get("capture", "auto_save")))
        self.chk_show_editor.setChecked(self.config.get("capture", "show_editor"))
        self.chk_startup.setChecked(self.config.get("system", "startup"))
        self.spin_delay.setValue(self.config.get("capture", "delay_seconds"))
        
        format_idx = self.combo_format.findText(self.config.get("capture", "image_format"))
        if format_idx >= 0:
            self.combo_format.setCurrentIndex(format_idx)
            
        self.edit_save_dir.setText(self.config.get("paths", "save_directory"))
        
        def _clean(hk):
            return hk.replace('<', '').replace('>', '')
            
        self.hk_simple.setText(_clean(self.config.get("hotkeys", "simple_capture")))
        self.hk_full.setText(_clean(self.config.get("hotkeys", "fullscreen_capture")))
        self.hk_window.setText(_clean(self.config.get("hotkeys", "window_capture")))
        self.hk_region.setText(_clean(self.config.get("hotkeys", "region_capture")))
        self.hk_size.setText(_clean(self.config.get("hotkeys", "size_capture")))
        self.hk_repeat.setText(_clean(self.config.get("hotkeys", "repeat_capture") or "ctrl+alt+r"))
 
    def save_settings(self):
        self.config.set("capture", "auto_copy_clipboard", self.chk_auto_copy.isChecked())
        self.config.set("capture", "auto_save", self.chk_auto_save.isChecked())
        self.config.set("capture", "show_editor", self.chk_show_editor.isChecked())
        self.config.set("system", "startup", self.chk_startup.isChecked())
        self.config.set("capture", "delay_seconds", self.spin_delay.value())
        self.config.set("capture", "image_format", self.combo_format.currentText())
        
        self.config.set("paths", "save_directory", self.edit_save_dir.text())
        
        def _clean(hk):
            return hk.replace('<', '').replace('>', '')
            
        self.config.set("hotkeys", "simple_capture", _clean(self.hk_simple.text()))
        self.config.set("hotkeys", "fullscreen_capture", _clean(self.hk_full.text()))
        self.config.set("hotkeys", "window_capture", _clean(self.hk_window.text()))
        self.config.set("hotkeys", "region_capture", _clean(self.hk_region.text()))
        self.config.set("hotkeys", "size_capture", _clean(self.hk_size.text()))
        self.config.set("hotkeys", "repeat_capture", _clean(self.hk_repeat.text()))
        
        # Reload hotkeys dynamically
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if hasattr(app, 'tray_icon'):
            app.tray_icon.refresh_labels()
        if hasattr(app, 'hotkey_manager'):
            app.hotkey_manager.start()
            failed = getattr(app.hotkey_manager, 'failed_hotkeys', [])
            if failed:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "단축키 등록 실패",
                                    "다음 단축키는 다른 프로그램이 사용 중입니다:\n"
                                    + "\n".join(failed))

        self.accept()
