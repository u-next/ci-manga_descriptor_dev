"""
Centralized Logging System for Manga Agent Runner

This module provides unified logging configuration for the entire manga description 
processing pipeline, including GCP operations, workflow processing, model interactions,
and I/O operations.

Functions:
    setup_logger: Configure and return the main logger instance
    get_logger: Get logger instance (singleton pattern)
    log_performance: Decorator for performance timing
    log_pipeline_stage: Context manager for pipeline stage logging
"""

import os
import logging
import functools
import time
from datetime import datetime
from typing import Optional, Any
from contextlib import contextmanager

# Global logger instance
_logger_instance = None


def setup_logger(
    name: str = "manga_agent_runner",
    level: str = "INFO", 
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    include_console: bool = True
) -> logging.Logger:
    """
    Configure and return the main logger instance.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output (with timestamp if not provided)
        format_string: Custom log format string
        include_console: Whether to include console output
        
    Returns:
        Configured logger instance
    """
    global _logger_instance
    
    if format_string is None:
        format_string = '%(asctime)s | %(name)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s'
    
    # Generate timestamped log file if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/manga_agent_runner_{timestamp}.log"
    
    # Clear any existing handlers
    if _logger_instance:
        for handler in _logger_instance.handlers[:]:
            _logger_instance.removeHandler(handler)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    if include_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"📁 Logging to file: {log_file}")
    
    logger.info(f"🚀 Manga Agent Runner logging initialized at {level} level")
    logger.info(f"📋 Logger: {name}")
    
    _logger_instance = logger
    return logger


def get_logger() -> logging.Logger:
    """
    Get the global logger instance (singleton pattern).
    
    Returns:
        Logger instance, creating default if none exists
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = setup_logger()
    
    return _logger_instance


def log_performance(operation_name: str = None):
    """
    Decorator to log function execution time and performance.
    
    Args:
        operation_name: Custom name for the operation (uses function name if not provided)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            logger.info(f"⏱️ Starting {op_name}")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"✅ Completed {op_name} in {execution_time:.3f}s")
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"❌ Failed {op_name} after {execution_time:.3f}s: {str(e)}")
                raise
                
        return wrapper
    return decorator


@contextmanager
def log_pipeline_stage(stage_name: str, details: dict = None):
    """
    Context manager for logging pipeline stages with entry/exit and error handling.
    
    Args:
        stage_name: Name of the pipeline stage
        details: Optional dictionary with stage details
    """
    logger = get_logger()
    
    # Format details if provided
    details_str = ""
    if details:
        details_list = [f"{k}={v}" for k, v in details.items()]
        details_str = f" ({', '.join(details_list)})"
    
    logger.info(f"🏗️ Starting pipeline stage: {stage_name}{details_str}")
    start_time = time.time()
    
    try:
        yield logger
        execution_time = time.time() - start_time
        logger.info(f"✅ Pipeline stage completed: {stage_name} in {execution_time:.3f}s")
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ Pipeline stage failed: {stage_name} after {execution_time:.3f}s: {str(e)}")
        raise


def log_gcp_operation(operation: str, project_id: str = None, details: dict = None):
    """
    Helper function for logging GCP-specific operations.
    
    Args:
        operation: Description of the GCP operation
        project_id: GCP project ID (if relevant)
        details: Additional operation details
    """
    logger = get_logger()
    
    details_str = ""
    if details:
        details_list = [f"{k}={v}" for k, v in details.items()]
        details_str = f" | {', '.join(details_list)}"
    
    project_str = f" | project={project_id}" if project_id else ""
    
    logger.info(f"☁️ GCP: {operation}{project_str}{details_str}")


def log_model_operation(operation: str, model_name: str = None, details: dict = None):
    """
    Helper function for logging AI model operations.
    
    Args:
        operation: Description of the model operation
        model_name: Name of the AI model
        details: Additional operation details (tokens, latency, etc.)
    """
    logger = get_logger()
    
    details_str = ""
    if details:
        details_list = [f"{k}={v}" for k, v in details.items()]
        details_str = f" | {', '.join(details_list)}"
    
    model_str = f" | model={model_name}" if model_name else ""
    
    logger.info(f"🧠 AI: {operation}{model_str}{details_str}")


def log_data_operation(operation: str, data_type: str = None, details: dict = None):
    """
    Helper function for logging data I/O operations.
    
    Args:
        operation: Description of the data operation
        data_type: Type of data being processed
        details: Additional operation details (file size, record count, etc.)
    """
    logger = get_logger()
    
    details_str = ""
    if details:
        details_list = [f"{k}={v}" for k, v in details.items()]
        details_str = f" | {', '.join(details_list)}"
    
    type_str = f" | type={data_type}" if data_type else ""
    
    logger.info(f"📊 Data: {operation}{type_str}{details_str}")