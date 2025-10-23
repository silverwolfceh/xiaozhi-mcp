# log_config.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(log_dir="logs", log_level=logging.INFO):
    """Set up logging configuration for the entire application."""
    # Makedirs
    os.makedirs(log_dir, exist_ok=True)
    # Create log filename with basic information
    log_file = os.path.join(log_dir, "app.log")
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create handlers
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10485760, backupCount=5
    )
    console_handler = logging.StreamHandler()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    if log_level > logging.DEBUG:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Set formatter for handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

def disable_logging(cfg):
    # print(cfg)
    for m in cfg:
        logging.getLogger(m).setLevel(logging.ERROR)
