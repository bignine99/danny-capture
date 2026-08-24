import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import platform

def setup_logger():
    if platform.system() == "Windows":
        app_data = Path(os.environ.get('APPDATA', str(Path.home())))
    else:
        app_data = Path.home() / ".config"
        
    log_dir = app_data / "Danny_Capture" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "app.log"
    
    logger = logging.getLogger("DannyCapture")
    logger.setLevel(logging.DEBUG)
    
    # Only add handlers if none exist to avoid duplicates
    if not logger.handlers:
        # Rotating file handler (5MB max per file, keep 3 backups)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger

def get_logger():
    return logging.getLogger("DannyCapture")
