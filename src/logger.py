"""
Logger for EC2 Auto-Shutdown Lambda

This module provides structured logging with JSON formatting for CloudWatch Logs Insights.
All log messages include timestamp, log level, and message, with support for additional
structured fields.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict


class Logger:
    """
    Structured logger for CloudWatch Logs with JSON formatting.
    
    This logger formats all messages as JSON objects for easy querying in
    CloudWatch Logs Insights. Each log entry includes:
    - timestamp: ISO 8601 formatted timestamp
    - level: Log level (INFO, WARNING, ERROR)
    - message: Human-readable message
    - Additional structured fields via kwargs
    
    Example:
        logger = Logger()
        logger.info("Instance stopped", instance_id="i-123", state="stopped")
        # Output: {"timestamp": "2024-01-01T12:00:00Z", "level": "INFO", 
        #          "message": "Instance stopped", "instance_id": "i-123", "state": "stopped"}
    """
    
    def __init__(self, name: str = "ec2-auto-shutdown"):
        """
        Initialize the logger.
        
        Args:
            name: Logger name (default: "ec2-auto-shutdown")
        """
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to avoid duplicates
        self._logger.handlers.clear()
        
        # Create console handler for Lambda (Lambda captures stdout/stderr)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # Use basic formatter since we'll format as JSON in our methods
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        self._logger.addHandler(handler)
    
    def _format_log(self, level: str, message: str, **kwargs: Any) -> str:
        """
        Format log message as JSON.
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            message: Human-readable message
            **kwargs: Additional structured fields
        
        Returns:
            JSON-formatted log string
        """
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message
        }
        
        # Add any additional structured fields
        if kwargs:
            log_entry.update(kwargs)
        
        return json.dumps(log_entry)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """
        Log informational message.
        
        Args:
            message: Human-readable message
            **kwargs: Additional structured fields (e.g., instance_id="i-123")
        
        Example:
            logger.info("Starting execution", region="us-east-1")
        """
        log_message = self._format_log("INFO", message, **kwargs)
        self._logger.info(log_message)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Log warning message.
        
        Args:
            message: Human-readable message
            **kwargs: Additional structured fields (e.g., instance_id="i-123")
        
        Example:
            logger.warning("Instance already stopped", instance_id="i-123")
        """
        log_message = self._format_log("WARNING", message, **kwargs)
        self._logger.warning(log_message)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """
        Log error message.
        
        Args:
            message: Human-readable message
            **kwargs: Additional structured fields (e.g., error_type="PermissionError")
        
        Example:
            logger.error("Failed to stop instance", instance_id="i-123", 
                        error_type="InsufficientInstanceCapacity")
        """
        log_message = self._format_log("ERROR", message, **kwargs)
        self._logger.error(log_message)
