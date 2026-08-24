from PySide6.QtGui import QScreen
from PySide6.QtWidgets import QApplication

def get_screen_scale_factor(screen: QScreen = None) -> float:
    """
    Returns the logical DPI scale factor of the given screen.
    If no screen is provided, it uses the primary screen.
    """
    if screen is None:
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            
    if screen:
        # Standard DPI is 96.
        return screen.logicalDotsPerInch() / 96.0
    return 1.0

def scale_value(value: int, screen: QScreen = None) -> int:
    """
    Scales a pixel value according to the screen's DPI scale factor.
    """
    return int(value * get_screen_scale_factor(screen))
