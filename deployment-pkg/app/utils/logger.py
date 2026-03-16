"""
Logging configuration for the platform.
"""
import logging
import sys
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Set logging level (default to INFO if settings not available yet)
        try:
            from config.settings import settings
            log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
        except Exception:
            log_level = logging.INFO
        logger.setLevel(log_level)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger
