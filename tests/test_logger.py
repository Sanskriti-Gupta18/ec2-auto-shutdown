"""
Unit tests for Logger class

Tests the structured logging functionality including JSON formatting,
log levels, and additional structured fields.
"""

import json
import logging
from io import StringIO
from unittest.mock import patch

import pytest

from src.logger import Logger


class TestLogger:
    """Test suite for Logger class"""
    
    def test_info_logs_with_correct_level(self):
        """Test that info() logs with INFO level"""
        logger = Logger()
        
        with patch.object(logger._logger, 'info') as mock_info:
            logger.info("Test message")
            
            # Verify info was called
            assert mock_info.called
            
            # Parse the JSON log message
            log_json = json.loads(mock_info.call_args[0][0])
            assert log_json["level"] == "INFO"
            assert log_json["message"] == "Test message"
    
    def test_warning_logs_with_correct_level(self):
        """Test that warning() logs with WARNING level"""
        logger = Logger()
        
        with patch.object(logger._logger, 'warning') as mock_warning:
            logger.warning("Test warning")
            
            # Verify warning was called
            assert mock_warning.called
            
            # Parse the JSON log message
            log_json = json.loads(mock_warning.call_args[0][0])
            assert log_json["level"] == "WARNING"
            assert log_json["message"] == "Test warning"
    
    def test_error_logs_with_correct_level(self):
        """Test that error() logs with ERROR level"""
        logger = Logger()
        
        with patch.object(logger._logger, 'error') as mock_error:
            logger.error("Test error")
            
            # Verify error was called
            assert mock_error.called
            
            # Parse the JSON log message
            log_json = json.loads(mock_error.call_args[0][0])
            assert log_json["level"] == "ERROR"
            assert log_json["message"] == "Test error"
    
    def test_log_includes_timestamp(self):
        """Test that all logs include ISO 8601 timestamp"""
        logger = Logger()
        
        with patch.object(logger._logger, 'info') as mock_info:
            logger.info("Test message")
            
            log_json = json.loads(mock_info.call_args[0][0])
            assert "timestamp" in log_json
            # Verify it ends with 'Z' for UTC
            assert log_json["timestamp"].endswith("Z")
            # Verify it contains ISO format elements
            assert "T" in log_json["timestamp"]
    
    def test_log_includes_structured_fields(self):
        """Test that additional kwargs are included as structured fields"""
        logger = Logger()
        
        with patch.object(logger._logger, 'info') as mock_info:
            logger.info("Instance stopped", instance_id="i-123", state="stopped")
            
            log_json = json.loads(mock_info.call_args[0][0])
            assert log_json["instance_id"] == "i-123"
            assert log_json["state"] == "stopped"
    
    def test_log_with_multiple_structured_fields(self):
        """Test logging with multiple structured fields"""
        logger = Logger()
        
        with patch.object(logger._logger, 'error') as mock_error:
            logger.error(
                "Failed to stop instance",
                instance_id="i-abc123",
                error_type="InsufficientInstanceCapacity",
                error_message="Not enough capacity",
                region="us-east-1"
            )
            
            log_json = json.loads(mock_error.call_args[0][0])
            assert log_json["level"] == "ERROR"
            assert log_json["message"] == "Failed to stop instance"
            assert log_json["instance_id"] == "i-abc123"
            assert log_json["error_type"] == "InsufficientInstanceCapacity"
            assert log_json["error_message"] == "Not enough capacity"
            assert log_json["region"] == "us-east-1"
    
    def test_log_output_is_valid_json(self):
        """Test that log output is valid JSON that can be parsed"""
        logger = Logger()
        
        with patch.object(logger._logger, 'info') as mock_info:
            logger.info("Test", key1="value1", key2=123, key3=True)
            
            # Should not raise exception
            log_json = json.loads(mock_info.call_args[0][0])
            
            # Verify all fields are present
            assert log_json["message"] == "Test"
            assert log_json["key1"] == "value1"
            assert log_json["key2"] == 123
            assert log_json["key3"] is True
    
    def test_log_without_structured_fields(self):
        """Test logging with only message, no additional fields"""
        logger = Logger()
        
        with patch.object(logger._logger, 'info') as mock_info:
            logger.info("Simple message")
            
            log_json = json.loads(mock_info.call_args[0][0])
            # Should only have timestamp, level, and message
            assert "timestamp" in log_json
            assert log_json["level"] == "INFO"
            assert log_json["message"] == "Simple message"
            # Should not have extra keys beyond these three
            assert len(log_json) == 3
