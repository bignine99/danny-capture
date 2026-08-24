import mss
from PIL import Image
from PySide6.QtGui import QScreen
from PySide6.QtWidgets import QApplication

class CaptureEngine:
    def __init__(self):
        self.sct = mss.mss()

    def get_monitors(self):
        return self.sct.monitors

    def capture_fullscreen(self, monitor_idx=0) -> Image.Image:
        """
        Captures the entire screen.
        If monitor_idx is 0, it captures all monitors combined.
        If monitor_idx > 0, it captures that specific monitor.
        """
        monitor = self.sct.monitors[monitor_idx]
        sct_img = self.sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img

    def freeze_screen(self):
        """
        Grabs the whole virtual screen once, so a selection can be cropped from
        this frozen image later. Transient popups (menus, autocomplete dropdowns)
        vanish as soon as the overlay takes focus, so the shot must be taken
        before the overlay is shown - not when the user releases the mouse.
        Returns (image, origin) where origin is the virtual screen top-left.
        """
        monitor = self.sct.monitors[0]
        sct_img = self.sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img, (monitor["left"], monitor["top"])

    def crop_frozen(self, frozen: Image.Image, origin, x: int, y: int,
                    width: int, height: int) -> Image.Image:
        """
        Crops a region (in virtual screen coordinates) out of a frozen screenshot.
        """
        ox, oy = origin
        left = x - ox
        top = y - oy
        box = (max(0, left), max(0, top),
               min(frozen.width, left + width), min(frozen.height, top + height))
        if box[2] <= box[0] or box[3] <= box[1]:
            return frozen.crop((0, 0, 1, 1))
        return frozen.crop(box)

    def capture_region(self, x: int, y: int, width: int, height: int) -> Image.Image:
        """
        Captures a specific region on the virtual screen.
        """
        region = {"top": y, "left": x, "width": width, "height": height}
        sct_img = self.sct.grab(region)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img

    def capture_window(self, hwnd=None) -> Image.Image:
        """
        Captures a specific window using its handle.
        If hwnd is None, captures the foreground window.
        """
        import win32gui
        import win32con
        import ctypes
        
        if hwnd is None:
            hwnd = win32gui.GetForegroundWindow()
            
        if not hwnd:
            return self.capture_fullscreen()
            
        try:
            # We use DWM to get the actual visual bounds of the window
            # falling back to GetWindowRect if DWM fails
            import ctypes.wintypes
            rect = ctypes.wintypes.RECT()
            DWMWA_EXTENDED_FRAME_BOUNDS = 9
            res = ctypes.windll.dwmapi.DwmGetWindowAttribute(
                hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, 
                ctypes.byref(rect), ctypes.sizeof(rect)
            )
            if res == 0:
                x = rect.left
                y = rect.top
                width = rect.right - rect.left
                height = rect.bottom - rect.top
            else:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                x = left
                y = top
                width = right - left
                height = bottom - top
                
            return self.capture_region(x, y, width, height)
        except Exception as e:
            print(f"Error capturing window: {e}")
            return self.capture_fullscreen()
