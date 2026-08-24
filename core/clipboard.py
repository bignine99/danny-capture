from PySide6.QtGui import QImage, QClipboard
from PySide6.QtWidgets import QApplication
from PIL import Image
import io

def copy_image_to_clipboard(image: Image.Image):
    """
    Copies a PIL Image to the system clipboard.
    """
    app = QApplication.instance()
    if not app:
        return
        
    clipboard = app.clipboard()
    
    # Convert PIL Image to RGBA mode if it isn't already
    if image.mode != "RGBA":
        image = image.convert("RGBA")
        
    data = image.tobytes("raw", "RGBA")
    qim = QImage(data, image.size[0], image.size[1], QImage.Format_RGBA8888).copy()
    
    clipboard.setImage(qim)

def copy_filepath_to_clipboard(filepath: str):
    """
    Copies a file path string to the system clipboard.
    """
    app = QApplication.instance()
    if not app:
        return
        
    clipboard = app.clipboard()
    clipboard.setText(filepath)
