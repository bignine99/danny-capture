from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsView, QGraphicsScene, QApplication, QColorDialog, QInputDialog, QGraphicsTextItem, QGraphicsPathItem, QGraphicsEllipseItem, QGraphicsSimpleTextItem, QFrame, QLabel, QMenu
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QPainterPath, QFont, qGray
from PySide6.QtCore import Qt, QPointF, QRectF, QLineF, QEvent, QTimer
from PIL import Image
from PIL.ImageQt import ImageQt
import math

NUMBER_LABELS = "①②③④⑤"

def apply_mica(hwnd):
    import ctypes
    try:
        # DWMWA_SYSTEMBACKDROP_TYPE = 38
        # 2 = DWMSBT_MAINWINDOW (Mica), 3 = DWMSBT_TRANSIENTWINDOW (Acrylic)
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        ctypes.windll.dwmapi.DwmSetWindowAttribute(int(hwnd), 20, ctypes.byref(ctypes.c_int(1)), 4) # Dark mode
        ctypes.windll.dwmapi.DwmSetWindowAttribute(int(hwnd), 38, ctypes.byref(ctypes.c_int(2)), 4) # Mica
    except Exception:
        pass

class DrawingScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = "pen"
        self.drawing = False
        self.last_point = None
        self.current_item = None
        self.pen_color = QColor("#FF0000") # Default red
        self.pen_width = 3
        
        self.undo_stack = []
        self.redo_stack = []
        self.on_crop = None  # set by EditorWindow
        self.number = 1
        self.on_number_placed = None  # set by EditorWindow

    def commit_item(self, item):
        if item:
            self.undo_stack.append(item)
            self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            item = self.undo_stack.pop()
            self.removeItem(item)
            self.redo_stack.append(item)

    def redo(self):
        if self.redo_stack:
            item = self.redo_stack.pop()
            self.addItem(item)
            self.undo_stack.append(item)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.scenePos()
            
            if self.mode == "pen" or self.mode == "highlighter":
                self.current_item = QGraphicsPathItem()
                pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                if self.mode == "highlighter":
                    hl_color = QColor(self.pen_color)
                    hl_color.setAlpha(80)
                    pen = QPen(hl_color, self.pen_width * 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                self.current_item.setPen(pen)
                
                path = QPainterPath(self.last_point)
                self.current_item.setPath(path)
                self.addItem(self.current_item)
                
            elif self.mode == "rect":
                pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
                self.current_item = self.addRect(QRectF(self.last_point, self.last_point), pen)

            elif self.mode == "crop":
                pen = QPen(QColor(255, 255, 255), 2, Qt.DashLine)
                self.current_item = self.addRect(QRectF(self.last_point, self.last_point), pen)
                
            elif self.mode == "arrow":
                self.current_item = self.addLine(QLineF(self.last_point, self.last_point), QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

            elif self.mode == "text":
                text, ok = QInputDialog.getText(None, "텍스트 입력", "텍스트를 입력하세요:")
                if ok and text:
                    text_item = QGraphicsTextItem(text)
                    text_item.setDefaultTextColor(self.pen_color)
                    text_item.setFont(QFont("Pretendard", 16, QFont.Bold))
                    text_item.setPos(self.last_point)
                    self.addItem(text_item)
                    self.commit_item(text_item)
                self.drawing = False

            elif self.mode == "number":
                self.commit_item(self.add_number_item(self.last_point))
                if self.on_number_placed:
                    self.on_number_placed()
                self.drawing = False

        super().mousePressEvent(event)

    def add_number_item(self, pos):
        """Filled circle in the pen color with the current number, centered on pos."""
        radius = 15
        circle = QGraphicsEllipseItem(-radius, -radius, radius * 2, radius * 2)
        circle.setBrush(self.pen_color)
        circle.setPen(QPen(Qt.NoPen))
        label = QGraphicsSimpleTextItem(str(self.number), circle)
        label.setFont(QFont("Pretendard", 14, QFont.Bold))
        # Keep the digit readable on light pen colors
        label.setBrush(Qt.black if qGray(self.pen_color.rgb()) > 160 else Qt.white)
        br = label.boundingRect()
        label.setPos(-br.width() / 2, -br.height() / 2)
        circle.setPos(pos)
        self.addItem(circle)
        return circle

    def mouseMoveEvent(self, event):
        if self.drawing:
            if (self.mode == "pen" or self.mode == "highlighter") and self.current_item:
                path = self.current_item.path()
                path.lineTo(event.scenePos())
                self.current_item.setPath(path)
            elif self.mode in ("rect", "crop") and self.current_item:
                rect = QRectF(self.last_point, event.scenePos()).normalized()
                self.current_item.setRect(rect)
            elif self.mode == "arrow" and self.current_item:
                line = QLineF(self.last_point, event.scenePos())
                self.current_item.setLine(line)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False

            if self.mode == "crop":
                if self.current_item:
                    rect = self.current_item.rect()
                    self.removeItem(self.current_item)
                    self.current_item = None
                    if self.on_crop:
                        self.on_crop(rect)
                super().mouseReleaseEvent(event)
                return
            
            if self.mode == "arrow" and self.current_item:
                line = self.current_item.line()
                angle = line.angle()
                arrow_size = 15
                
                p1 = line.p2() - QPointF(math.sin(math.radians(angle + 60)) * arrow_size, math.cos(math.radians(angle + 60)) * arrow_size)
                p2 = line.p2() - QPointF(math.sin(math.radians(angle + 120)) * arrow_size, math.cos(math.radians(angle + 120)) * arrow_size)
                
                arrow_path = QPainterPath(line.p1())
                arrow_path.lineTo(line.p2())
                arrow_path.moveTo(p1)
                arrow_path.lineTo(line.p2())
                arrow_path.lineTo(p2)
                
                self.removeItem(self.current_item)
                self.current_item = self.addPath(arrow_path, QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

            if self.current_item:
                self.commit_item(self.current_item)
            self.current_item = None
            
        super().mouseReleaseEvent(event)

class ZoomableView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.setStyleSheet("background-color: transparent; border: none;")

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.scale(zoom_factor, zoom_factor)
        event.accept()

class EditorWindow(QWidget):
    def __init__(self, pil_image: Image.Image, on_save_callback=None, source_filepath=None):
        super().__init__()
        self.setWindowTitle("Danny Capture Editor")
        self.resize(1000, 700)
        
        # Apply Windows 11 Native Mica effect
        apply_mica(int(self.winId()))
        self.setStyleSheet("background-color: transparent;")
        
        self.on_save_callback = on_save_callback
        self.source_filepath = source_filepath
        self._color_dialog = None
        self.original_image = pil_image
        
        self.setup_ui()
        self.load_image(pil_image)

    def setup_ui(self):
        # We use absolute positioning or a custom layout for the floating toolbar
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = ZoomableView()
        self.scene = DrawingScene()
        self.view.setScene(self.scene)
        self.main_layout.addWidget(self.view)
        
        # Floating Toolbar Palette
        self.toolbar_container = QFrame(self)
        self.toolbar_container.setStyleSheet("""
            QFrame {
                background-color: rgba(35, 35, 35, 200);
                border-radius: 5px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton {
                background-color: transparent;
                color: white;
                border-radius: 5px;
                font-family: "Pretendard", "Segoe UI Emoji";
                font-size: 16px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QPushButton:checked {
                background-color: rgba(0, 180, 240, 0.3);
                border: 1px solid rgba(0, 180, 240, 0.5);
            }
        """)
        
        toolbar_layout = QHBoxLayout(self.toolbar_container)
        toolbar_layout.setContentsMargins(8, 8, 8, 8)
        toolbar_layout.setSpacing(4)
        
        self.btn_crop = QPushButton("✂ 자르기")
        self.btn_pen = QPushButton("✐ 펜")
        self.btn_hl = QPushButton("▧ 형광펜")
        self.btn_rect = QPushButton("□ 사각형")
        self.btn_arrow = QPushButton("↗ 화살표")
        self.btn_text = QPushButton("T 텍스트")
        self.btn_number = QPushButton("① 번호")
        self.btn_color = QPushButton("◑ 색상")
        
        self.btn_undo = QPushButton("↶ 취소")
        self.btn_redo = QPushButton("↷ 다시")
        self.btn_copy = QPushButton("📋 복사")
        self.btn_save = QPushButton("⤓ 저장")
        
        # Make tools checkable for exclusive selection
        self.tool_buttons = [self.btn_crop, self.btn_pen, self.btn_hl, self.btn_rect, self.btn_arrow, self.btn_text, self.btn_number]
        for btn in self.tool_buttons:
            btn.setCheckable(True)
            toolbar_layout.addWidget(btn)
        self.btn_pen.setChecked(True)
            
        toolbar_layout.addWidget(QLabel(" | "))
        toolbar_layout.addWidget(self.btn_color)
        toolbar_layout.addWidget(QLabel(" | "))
        toolbar_layout.addWidget(self.btn_undo)
        toolbar_layout.addWidget(self.btn_redo)
        toolbar_layout.addWidget(QLabel(" | "))
        toolbar_layout.addWidget(self.btn_copy)
        toolbar_layout.addWidget(self.btn_save)
        
        # Connect signals
        self.scene.on_crop = self.apply_crop
        self.btn_crop.clicked.connect(lambda: self.set_mode("crop", self.btn_crop))
        self.btn_pen.clicked.connect(lambda: self.set_mode("pen", self.btn_pen))
        self.btn_hl.clicked.connect(lambda: self.set_mode("highlighter", self.btn_hl))
        self.btn_rect.clicked.connect(lambda: self.set_mode("rect", self.btn_rect))
        self.btn_arrow.clicked.connect(lambda: self.set_mode("arrow", self.btn_arrow))
        self.btn_text.clicked.connect(lambda: self.set_mode("text", self.btn_text))
        self.scene.on_number_placed = self._advance_number
        self.btn_number.clicked.connect(self.choose_number)
        
        self.btn_color.clicked.connect(self.choose_color)
        self.btn_undo.clicked.connect(self.scene.undo)
        self.btn_redo.clicked.connect(self.scene.redo)
        self.btn_copy.clicked.connect(self.copy_image)
        self.btn_save.clicked.connect(self.save_image)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Center the floating toolbar at the bottom
        tw = self.toolbar_container.sizeHint().width()
        th = self.toolbar_container.sizeHint().height()
        self.toolbar_container.setGeometry((self.width() - tw) // 2, self.height() - th - 20, tw, th)

    def load_image(self, pil_image):
        qim = ImageQt(pil_image)
        pixmap = QPixmap.fromImage(qim)
        self.scene.clear()
        self.scene.undo_stack.clear()
        self.scene.redo_stack.clear()
        
        # Add shadow to pixmap in a real scenario, here we just add it
        self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(pixmap.rect())
        
        # Center view
        self.view.setSceneRect(pixmap.rect())

    def set_mode(self, mode, active_btn):
        # Re-clicking the active tool must not leave it unchecked while the
        # mode silently stays on (destructive for crop) — keep it checked.
        active_btn.setChecked(True)
        self.scene.mode = mode
        # Set cursor based on mode
        if mode == "text":
            self.view.setCursor(Qt.IBeamCursor)
        elif mode in ["pen", "highlighter", "crop", "number"]:
            self.view.setCursor(Qt.CrossCursor)
        else:
            self.view.setCursor(Qt.ArrowCursor)
            
        for btn in self.tool_buttons:
            if btn != active_btn:
                btn.setChecked(False)

    def apply_crop(self, rect):
        """Bake the current scene (image + annotations) and crop to rect."""
        scene_rect = self.scene.sceneRect()
        rect = rect.normalized().intersected(scene_rect)
        if rect.width() < 5 or rect.height() < 5:
            return

        image = QImage(scene_rect.size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        self.scene.render(painter)
        painter.end()

        cropped = image.copy(rect.toRect())
        pixmap = QPixmap.fromImage(cropped)

        # Annotations are baked into the crop; undo history is reset
        self.scene.clear()
        self.scene.undo_stack.clear()
        self.scene.redo_stack.clear()
        self.scene.current_item = None
        self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(QRectF(pixmap.rect()))
        self.view.setSceneRect(QRectF(pixmap.rect()))

    def choose_number(self):
        """Enter number mode and let the user pick which number (1-5) to stamp next."""
        self.set_mode("number", self.btn_number)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgb(35, 35, 35);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                font-family: "Pretendard", "Malgun Gothic";
                font-size: 16px;
            }
            QMenu::item:selected {
                background-color: rgba(0, 180, 240, 0.3);
            }
        """)
        for n, label in enumerate(NUMBER_LABELS, start=1):
            menu.addAction(f"{label}  {n}번").triggered.connect(lambda _=False, n=n: self._set_number(n))
        # Open upward — the toolbar sits at the bottom of the window
        top_left = self.btn_number.mapToGlobal(self.btn_number.rect().topLeft())
        top_left.setY(top_left.y() - menu.sizeHint().height())
        menu.exec(top_left)

    def _set_number(self, n):
        self.scene.number = n
        self.btn_number.setText(f"{NUMBER_LABELS[n - 1]} 번호")

    def _advance_number(self):
        # After stamping, move on to the next number so 1→2→3 needs no reselecting
        self._set_number(min(self.scene.number + 1, len(NUMBER_LABELS)))

    def choose_color(self):
        if self._color_dialog is not None:
            self._color_dialog.raise_()
            self._color_dialog.activateWindow()
            return
        dialog = QColorDialog(self.scene.pen_color, self)
        dialog.setOption(QColorDialog.ColorDialogOption.NoButtons)
        dialog.currentColorChanged.connect(self._on_color_changed)
        dialog.finished.connect(self._on_color_dialog_finished)
        # Non-modal, so a click on the editor reaches eventFilter and can close it.
        # Closes as soon as the user finishes picking (mouse release after a change),
        # or on any click outside the dialog.
        self._color_dialog = dialog
        self._color_picked = False
        QApplication.instance().installEventFilter(self)
        dialog.show()

    def _on_color_dialog_finished(self):
        QApplication.instance().removeEventFilter(self)
        self._color_dialog.deleteLater()
        self._color_dialog = None

    def _close_color_dialog_if_picked(self):
        if self._color_dialog is not None and self._color_picked:
            self._color_dialog.accept()

    def eventFilter(self, obj, event):
        dialog = self._color_dialog
        if dialog is not None:
            if event.type() == QEvent.MouseButtonRelease:
                # A swatch click changes the color while this release is being
                # handled, so check only after the event has been delivered.
                QTimer.singleShot(0, self._close_color_dialog_if_picked)
            elif (event.type() == QEvent.MouseButtonPress and isinstance(obj, QWidget)
                    and obj.window() is not dialog):
                dialog.accept()
                return True
        return super().eventFilter(obj, event)

    def _on_color_changed(self, color):
        if color.isValid():
            self.scene.pen_color = color
            self._color_picked = True

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self.scene.undo()
            elif event.key() == Qt.Key_Y:
                self.scene.redo()
            elif event.key() == Qt.Key_C:
                self.copy_image()
            elif event.key() == Qt.Key_S:
                self.save_image()
        super().keyPressEvent(event)

    def copy_image(self):
        rect = self.scene.sceneRect()
        image = QImage(rect.size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        self.scene.render(painter)
        painter.end()
        
        pixmap = QPixmap.fromImage(image)
        QApplication.clipboard().setPixmap(pixmap)
        
        # Optional: Show visual feedback
        self.btn_copy.setText("✔ 복사됨!")
        self.btn_copy.setStyleSheet("background-color: rgba(0, 200, 100, 0.3);")
        
        from PySide6.QtCore import QTimer
        def restore_btn():
            self.btn_copy.setText("📋 복사")
            self.btn_copy.setStyleSheet("")
        QTimer.singleShot(2000, restore_btn)

    def save_image(self):
        rect = self.scene.sceneRect()
        image = QImage(rect.size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        self.scene.render(painter)
        painter.end()
        
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from utils.file_manager import FileManager
        
        if self.source_filepath:
            # Overwrite the auto-saved capture instead of creating a second file
            default_filepath = str(self.source_filepath)
        else:
            # The configured folder may be the very reason auto-save failed —
            # this dialog is the rescue path, so it must never die on it.
            try:
                fm = FileManager()
                default_filepath = str(fm.get_new_filepath("capture_edited"))
            except Exception:
                from pathlib import Path as _P
                default_filepath = str(_P.home() / "Pictures" / "capture_edited.png")

        file_path, _ = QFileDialog.getSaveFileName(self, "저장하기", default_filepath, "PNG Images (*.png);;JPEG Images (*.jpg)")

        if file_path:
            try:
                ok = image.save(file_path)
            except Exception:
                ok = False
            if ok:
                QMessageBox.information(self, "저장 완료", f"이미지가 성공적으로 저장되었습니다:\n{file_path}")
                self.close()
            else:
                QMessageBox.critical(self, "저장 실패",
                                     f"이미지를 저장하지 못했습니다:\n{file_path}\n경로와 디스크 상태를 확인하세요.")

