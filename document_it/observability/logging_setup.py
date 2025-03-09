"""
Logging setup for Document-it.

This module provides functionality for configuring logging with enhanced
formatting and context.
"""

import os
import sys
import json
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Define log levels
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# Define a custom JSON formatter
class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    This formatter outputs log records as JSON objects with additional context.
    """
    
    def __init__(self, include_timestamp: bool = True):
        """
        Initialize the JSON formatter.
        
        Args:
            include_timestamp: Whether to include a timestamp in the log record
        """
        super().__init__()
        self.include_timestamp = include_timestamp
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as a JSON object.
        
        Args:
            record: The log record to format
            
        Returns:
            The formatted log record as a JSON string
        """
        log_data = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add timestamp if requested
        if self.include_timestamp:
            log_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Add file and line information
        log_data["file"] = record.pathname
        log_data["line"] = record.lineno
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the record
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        
        if hasattr(record, "document_id"):
            log_data["document_id"] = record.document_id
        
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        
        # Add any extra attributes from the record
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", 
                          "filename", "funcName", "id", "levelname", "levelno", 
                          "lineno", "module", "msecs", "message", "msg", 
                          "name", "pathname", "process", "processName", 
                          "relativeCreated", "stack_info", "thread", "threadName"]:
                try:
                    # Try to serialize the value to JSON
                    json.dumps({key: value})
                    log_data[key] = value
                except (TypeError, OverflowError):
                    # If the value can't be serialized, convert it to a string
                    log_data[key] = str(value)
        
        return json.dumps(log_data)


class ContextAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context to log records.
    
    This adapter allows adding context such as trace IDs, document IDs, and job IDs
    to log records.
    """
    
    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        """
        Initialize the context adapter.
        
        Args:
            logger: The logger to adapt
            extra: Extra context to add to log records
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process a log message and add context.
        
        Args:
            msg: The log message
            kwargs: Additional arguments for the log record
            
        Returns:
            The processed message and kwargs
        """
        # Ensure extra dict exists
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        
        # Add context from the adapter
        for key, value in self.extra.items():
            kwargs["extra"][key] = value
        
        return msg, kwargs
    
    def with_context(self, **context) -> "ContextAdapter":
        """
        Create a new adapter with additional context.
        
        Args:
            **context: Additional context to add
            
        Returns:
            A new context adapter with the additional context
        """
        new_extra = self.extra.copy()
        new_extra.update(context)
        return ContextAdapter(self.logger, new_extra)


def configure_logging(
    level: str = "info",
    log_file: Optional[str] = None,
    json_format: bool = True,
    console_output: bool = True
) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: The log level (debug, info, warning, error, critical)
        log_file: Path to a log file (optional)
        json_format: Whether to use JSON formatting
        console_output: Whether to output logs to the console
    """
    # Get the log level
    log_level = LOG_LEVELS.get(level.lower(), logging.INFO)
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_file:
        # Create the directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure the document-it logger
    document_it_logger = logging.getLogger("document-it")
    document_it_logger.setLevel(log_level)
    
    # Log the configuration
    document_it_logger.info(
        f"Logging configured with level={level}, "
        f"json_format={json_format}, "
        f"console_output={console_output}, "
        f"log_file={log_file}"
    )


def get_logger(name: str, **context) -> ContextAdapter:
    """
    Get a logger with context.
    
    Args:
        name: The logger name
        **context: Additional context to add to log records
        
    Returns:
        A context adapter for the logger
    """
    logger = logging.getLogger(name)
    
    # Add trace_id if not provided
    if "trace_id" not in context:
        context["trace_id"] = str(uuid.uuid4())
    
    return ContextAdapter(logger, context)