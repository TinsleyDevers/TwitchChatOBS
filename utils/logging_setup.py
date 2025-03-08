"""
Logging setup for the Twitch Tracker application.
"""
import logging
import os
import sys


def setup_logging(log_file="twitch_tracker.log", level=logging.INFO):
    """
    Configure logging for the application.
    
    Args:
        log_file: Name of the log file
        level: Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    logger = logging.getLogger("TwitchTracker")
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized to {log_file}")
    
    return logger