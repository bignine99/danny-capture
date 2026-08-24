from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPainter, QColor, QPen, QCursor, QPainterPath, QPixmap, QFont
from PySide6.QtCore import Qt, QRect, QPoint, QSize

class CaptureOverlay(QWidget):
    def __init__(self, mode="region", fixed_size=None):
        super().__init__()
        self.mode = mode # "region", "window", "screen", "fixed_size"
        self.fixed_size = fixed_size # QSize for fixed_size mode
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True) # Essential for Loupe tool
        
        # Determine geometry of all screens combined
        self.desktop_rect = QApplication.instance().primaryScreen().virtualGeometry()
        for screen in QApplication.instance().screens():
            self.desktop_rect = self.desktop_rect.united(screen.geometry())
            
        self.setGeometry(self.desktop_rect)
        
        self.start_pos = None
        self.current_pos = None
        self.mouse_pos = QPoint(-1000, -1000)
        self.selected_rect = QRect()
        self.hover_rect = QRect()
        
        # Captured result callback
        self.on_capture = None

        # Freeze the screen now, while the overlay is built but not yet shown.
        # Showing it steals focus and closes any open menu/dropdown, so the
        # final image must be cropped from this frozen shot.
        from core.capture import CaptureEngine
        self.frozen_image, self.frozen_origin = CaptureEngine().freeze_screen()

        # The frozen shot doubles as the overlay background and the loupe
        # source, so the screen *looks* frozen too: transient popups stay
        # visible while selecting, and what you see is exactly what is cropped.
        from PIL.ImageQt import ImageQt
        self.bg_pixmap = QPixmap.fromImage(ImageQt(self.frozen_image))
        self.bg_offset = QPoint(self.frozen_origin[0], self.frozen_origin[1]) - self.desktop_rect.topLeft()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Frozen screen as the backdrop, dimmed on top
        painter.drawPixmap(self.bg_offset, self.bg_pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        
        target_rect = None
        if self.mode == "region":
            if self.start_pos and self.current_pos:
                target_rect = QRect(self.start_pos, self.current_pos).normalized()
        else:
            target_rect = self.hover_rect
            
        if target_rect and not target_rect.isEmpty():
            # Local rect for painting (relative to self.rect())
            local_rect = target_rect.translated(-self.desktop_rect.topLeft())
            local_rect = local_rect.intersected(self.rect())
            
            # Reveal the selected area at full brightness from the frozen shot
            painter.drawPixmap(local_rect, self.bg_pixmap,
                               local_rect.translated(-self.bg_offset))

            # Draw border
            pen = QPen(QColor("#00B4F0"), 2)
            painter.setPen(pen)
            painter.drawRect(local_rect)
            
            # Draw dimension badge
            text = f" {target_rect.width()} x {target_rect.height()} "
            painter.setFont(QFont("Outfit", 12, QFont.Bold))
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(text)
            th = fm.height()
            
            badge_rect = QRect(local_rect.bottomRight().x() - tw - 10, 
                               local_rect.bottomRight().y() + 10, 
                               tw + 10, th + 10)
                               
            # Ensure badge doesn't go off-screen
            if badge_rect.bottom() > self.rect().bottom():
                badge_rect.moveBottom(local_rect.top() - 10)
            if badge_rect.right() > self.rect().right():
                badge_rect.moveRight(self.rect().right() - 10)
                
            painter.setBrush(QColor(30, 30, 30, 220))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(badge_rect, 5, 5)
            
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(badge_rect, Qt.AlignCenter, text)

        # Draw Loupe (Magnifier)
        local_mouse = self.mouse_pos - self.desktop_rect.topLeft()
        if self.rect().contains(local_mouse):
            loupe_radius = 60
            zoom_factor = 3
            src_size = loupe_radius * 2 // zoom_factor
            
            src_rect = QRect(local_mouse.x() - src_size // 2, 
                             local_mouse.y() - src_size // 2, 
                             src_size, src_size)
                             
            # Position loupe to the bottom right of the cursor
            loupe_pos = local_mouse + QPoint(20, 20)
            
            # Prevent loupe from going off-screen
            if loupe_pos.x() + loupe_radius * 2 > self.rect().right():
                loupe_pos.setX(local_mouse.x() - loupe_radius * 2 - 20)
            if loupe_pos.y() + loupe_radius * 2 > self.rect().bottom():
                loupe_pos.setY(local_mouse.y() - loupe_radius * 2 - 20)
                
            loupe_rect = QRect(loupe_pos.x(), loupe_pos.y(), loupe_radius * 2, loupe_radius * 2)
            
            # Clip to circle
            path = QPainterPath()
            path.addEllipse(loupe_rect)
            
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.save()
            painter.setClipPath(path)
            
            # Draw magnified image
            painter.drawPixmap(loupe_rect, self.bg_pixmap, src_rect)
            
            # Draw Crosshair inside loupe
            painter.setPen(QPen(QColor(0, 180, 240, 150), 1))
            painter.drawLine(loupe_rect.center().x(), loupe_rect.top(), loupe_rect.center().x(), loupe_rect.bottom())
            painter.drawLine(loupe_rect.left(), loupe_rect.center().y(), loupe_rect.right(), loupe_rect.center().y())
            
            painter.restore()
            
            # Draw Loupe border
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
            painter.drawEllipse(loupe_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.mode == "region":
                self.start_pos = event.globalPosition().toPoint()
                self.current_pos = self.start_pos
            self.mouse_pos = event.globalPosition().toPoint()
            self.update()
        elif event.button() == Qt.RightButton:
            self.close() # Cancel

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.globalPosition().toPoint()
        
        if self.mode == "region":
            if self.start_pos:
                self.current_pos = event.globalPosition().toPoint()
        elif self.mode == "window":
            try:
                import win32gui
                import win32con
                hwnd = win32gui.WindowFromPoint((self.mouse_pos.x(), self.mouse_pos.y()))
                root_hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
                if root_hwnd:
                    rect = win32gui.GetWindowRect(root_hwnd)
                    self.hover_rect = QRect(rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])
            except Exception:
                pass
        elif self.mode == "screen":
            for screen in QApplication.screens():
                if screen.geometry().contains(self.mouse_pos):
                    self.hover_rect = screen.geometry()
                    break
        elif self.mode == "fixed_size" and self.fixed_size:
            w, h = self.fixed_size.width(), self.fixed_size.height()
            self.hover_rect = QRect(self.mouse_pos.x() - w//2, self.mouse_pos.y() - h//2, w, h)
            
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.mode == "region":
                if self.start_pos:
                    self.current_pos = event.globalPosition().toPoint()
                    self.selected_rect = QRect(self.start_pos, self.current_pos).normalized()
            else:
                self.selected_rect = self.hover_rect
                
            self.hide() # Hide before capturing
            
            if self.selected_rect.width() > 0 and self.selected_rect.height() > 0:
                if self.on_capture:
                    # Pass the geometry relative to the virtual screen top-left
                    self.on_capture(self.selected_rect)
            
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
