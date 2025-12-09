import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name="ai_agent", log_level=logging.INFO):
    """
    Setup a centralized logger with Console and File handlers.
    """
    # Create logs directory if not exists
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log filename by date
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"agent_{today}.log")

    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. File Handler (Rotating)
    # Max 5MB per file, keep last 5 backpus
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # 2. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Global Logger Instance
logger = setup_logger()
