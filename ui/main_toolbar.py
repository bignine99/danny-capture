from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication, QInputDialog, QSystemTrayIcon
from PySide6.QtCore import Qt, QPoint, QRect, QTimer, QPropertyAnimation, QEasingCurve, QSize
from core.capture import CaptureEngine
from ui.overlay import CaptureOverlay
from ui.editor import EditorWindow
from ui.settings_dialog import SettingsDialog
from core.clipboard import copy_image_to_clipboard
from utils.file_manager import FileManager
from ui.notification import NotificationManager

class MainToolbar(QWidget):
    def __init__(self, parent=None):
        if parent is None:
            self.dummy_parent = QWidget()
            parent = self.dummy_parent
        super().__init__(parent)
        
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.drag_pos = QPoint()
        self.editors = []  # keep every open editor alive until its window closes
        self.capture_engine = CaptureEngine()
        self.file_manager = FileManager()
        self.notifier = NotificationManager()
        
        self.setup_ui()
        self.apply_styles()
        self.connect_signals()
        
        # Initialize accordion animation
        self.anim = QPropertyAnimation(self.ext_widget, b"maximumWidth")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutExpo)
        self.ext_widget.setMaximumWidth(0)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Container for Pill shape
        self.container = QWidget()
        self.container.setObjectName("container")
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)
        
        # Drag handle / Logo
        self.drag_label = QLabel("99 Capture")
        self.drag_label.setAlignment(Qt.AlignCenter)
        self.drag_label.setFixedHeight(40)
        self.drag_label.setContentsMargins(15, 0, 10, 0)
        self.drag_label.setStyleSheet("font-weight: bold; color: #00B4F0; font-size: 14px; font-family: 'Outfit', 'Pretendard', sans-serif; letter-spacing: 0.5px;")
        container_layout.addWidget(self.drag_label)
        
        # Primary Action Button
        self.btn_simple = QPushButton("간편 캡처")
        self.btn_simple.setObjectName("btn_simple")
        self.btn_simple.setFixedSize(90, 40)
        container_layout.addWidget(self.btn_simple)
        
        # Extended Buttons Container (Accordion part)
        self.ext_widget = QWidget()
        ext_layout = QHBoxLayout(self.ext_widget)
        ext_layout.setContentsMargins(0, 0, 0, 0)
        ext_layout.setSpacing(5)
        
        self.btn_full = QPushButton("전체")
        self.btn_window = QPushButton("창")
        self.btn_region = QPushButton("단위")
        self.btn_size = QPushButton("크기")
        self.btn_settings = QPushButton("⚙️")
        self.btn_close = QPushButton("❌")
        
        for btn in [self.btn_full, self.btn_window, self.btn_region, self.btn_size]:
            btn.setFixedSize(50, 40)
            ext_layout.addWidget(btn)
            
        for btn in [self.btn_settings, self.btn_close]:
            btn.setFixedSize(40, 40)
            ext_layout.addWidget(btn)
            
        container_layout.addWidget(self.ext_widget)
        layout.addWidget(self.container)

    def connect_signals(self):
        self.btn_simple.clicked.connect(self.start_simple_capture)
        self.btn_full.clicked.connect(self.start_full_capture)
        self.btn_size.clicked.connect(self.start_size_capture)
        
        # Mapping advanced captures
        self.btn_window.clicked.connect(self.start_window_capture)
        self.btn_region.clicked.connect(self.start_simple_capture)
        
        self.btn_settings.clicked.connect(self.show_settings)
        self.btn_close.clicked.connect(self.hide_window)

    def hide_window(self):
        self.hide()

    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def _handle_capture_result(self, img):
        if not img:
            return

        config = self.file_manager.config

        # 1. Copy to clipboard
        copied = bool(config.get("capture", "auto_copy_clipboard"))
        if copied:
            copy_image_to_clipboard(img)

        # 2. Save file (honors auto_save; failure must not lose the capture)
        filepath = None
        if config.get("capture", "auto_save"):
            try:
                filepath = self.file_manager.get_new_filepath()
                img.save(filepath)
            except Exception:
                filepath = None
                self.notifier.show_message("저장 실패", "저장 폴더에 쓸 수 없습니다. 환경설정에서 저장 폴더를 확인하세요.")

        # 3. Notify
        if filepath:
            self.notifier.show_capture_success(str(filepath), "저장 및 클립보드 복사 완료" if copied else None)
        elif copied:
            self.notifier.show_message("캡쳐 완료", "클립보드 복사 완료")

        # 4. Show Editor (editor saves over the auto-saved file, not a second one)
        if config.get("capture", "show_editor"):
            editor = EditorWindow(img, source_filepath=filepath)
            # A bare re-assignment would garbage-collect the previous editor
            # window mid-edit; keep each one alive until the user closes it.
            editor.setAttribute(Qt.WA_DeleteOnClose)
            self.editors.append(editor)
            editor.destroyed.connect(
                lambda *_, e=editor: e in self.editors and self.editors.remove(e))
            self.editor = editor
            editor.show()

    def start_simple_capture(self):
        self.hide()
        # Delay slightly to ensure window is hidden
        QTimer.singleShot(100, self._show_overlay_region)

    def _show_overlay_region(self):
        self.overlay = CaptureOverlay(mode="region")
        self.overlay.on_capture = self._on_region_captured
        self.overlay.show()

    def _on_region_captured(self, rect: QRect):
        # Remember the region so it can be re-captured with one hotkey
        self.file_manager.config.set(
            "capture", "last_region", [rect.x(), rect.y(), rect.width(), rect.height()])
        img = self.capture_engine.crop_frozen(
            self.overlay.frozen_image, self.overlay.frozen_origin,
            rect.x(), rect.y(), rect.width(), rect.height())
        self._handle_capture_result(img)

    def start_repeat_capture(self):
        """Re-capture the last used region instantly, without an overlay."""
        region = self.file_manager.config.get("capture", "last_region")
        if not region:
            self.notifier.show_message("재캡처 불가", "저장된 영역이 없습니다. 먼저 영역 캡처를 한 번 하세요.")
            return
        # Clamp to the current virtual screen: after a monitor change the
        # stored region may be off-screen and mss would return black pixels.
        x, y, w, h = region
        virtual = QApplication.primaryScreen().virtualGeometry()
        for s in QApplication.screens():
            virtual = virtual.united(s.geometry())
        clamped = QRect(x, y, w, h).intersected(virtual)
        if clamped.isEmpty():
            self.notifier.show_message("재캡처 불가", "저장된 영역이 현재 화면 밖에 있습니다. 다시 영역 캡처를 하세요.")
            return
        self.hide()
        QTimer.singleShot(100, lambda: self._handle_capture_result(
            self.capture_engine.capture_region(
                clamped.x(), clamped.y(), clamped.width(), clamped.height())))

    def start_full_capture(self):
        self.hide()
        QTimer.singleShot(100, self._show_overlay_screen)

    def _show_overlay_screen(self):
        self.overlay = CaptureOverlay(mode="screen")
        self.overlay.on_capture = self._on_region_captured
        self.overlay.show()

    def start_size_capture(self):
        self.hide()
        width, ok1 = QInputDialog.getInt(self, "가로 크기", "Width (px):", 800, 10, 4000)
        if not ok1:
            return
        height, ok2 = QInputDialog.getInt(self, "세로 크기", "Height (px):", 600, 10, 4000)
        if not ok2:
            return
            
        QTimer.singleShot(100, lambda: self._show_overlay_fixed_size(width, height))
        
    def _show_overlay_fixed_size(self, w, h):
        self.overlay = CaptureOverlay(mode="fixed_size", fixed_size=QSize(w, h))
        self.overlay.on_capture = self._on_region_captured
        self.overlay.show()

    def start_window_capture(self):
        self.hide()
        QTimer.singleShot(100, self._show_overlay_window)

    def _show_overlay_window(self):
        self.overlay = CaptureOverlay(mode="window")
        self.overlay.on_capture = self._on_region_captured
        self.overlay.show()
        

        
    def apply_styles(self):
        self.setStyleSheet("""
            #container {
                background-color: rgba(30, 30, 30, 230);
                border-radius: 5px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            #btn_simple {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0078D4, stop:1 #00B4F0);
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-family: "Pretendard", "Outfit", "Malgun Gothic";
                font-size: 14px;
            }
            #btn_simple:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0089F5, stop:1 #1AD0FF);
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.05);
                color: white;
                border: 1px solid transparent;
                border-radius: 5px;
                font-family: "Pretendard", "Outfit", "Malgun Gothic";
                font-size: 13px;
                transition: background-color 0.2s ease;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.02);
            }
        """)

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.ext_widget.maximumWidth())
        self.anim.setEndValue(310) # 50*4 + 40*2 + spacing = approx 310
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.ext_widget.maximumWidth())
        self.anim.setEndValue(0)
        self.anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def show_normal(self):
        self.show()
        self.activateWindow()

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        context_menu = QMenu(self)
        context_menu.setStyleSheet("""
            QMenu {
                background-color: rgb(35, 35, 35);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                font-family: "Pretendard", "Malgun Gothic";
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: rgba(0, 180, 240, 0.3);
            }
        """)
        
        action_settings = QAction("⚙️ 환경설정", self)
        action_exit = QAction("❌ 프로그램 종료", self)
        
        action_settings.triggered.connect(self.show_settings)
        action_exit.triggered.connect(QApplication.quit)
        
        context_menu.addAction(action_settings)
        context_menu.addAction(action_exit)
        
        context_menu.exec(event.globalPos())
