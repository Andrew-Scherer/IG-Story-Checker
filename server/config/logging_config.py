"""
Logging Configuration
Handles setup of logging for different components
"""

import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from flask import Blueprint

def setup_component_logging(name: str, log_dir: str = 'logs') -> logging.Logger:
    """Set up logging for a component
    
    Args:
        name: Name of the component (e.g., 'batch', 'worker')
        log_dir: Directory to store log files
        
    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), log_dir)
    os.makedirs(log_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create rotating file handler
    log_file = os.path.join(log_dir, f'{name}_debug.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Add test log message
    logger.debug(f"Logging initialized for {name} operations")

    return logger

def setup_blueprint_logging(blueprint: Blueprint, name: str) -> logging.Logger:
    """Set up logging for a Flask blueprint
    
    Args:
        blueprint: Flask blueprint to set up logging for
        name: Name of the component
        
    Returns:
        Configured logger instance
    """
    logger = setup_component_logging(name)
    blueprint.logger = logger
    return logger
