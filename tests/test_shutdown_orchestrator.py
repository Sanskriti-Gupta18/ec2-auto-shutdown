"""
Unit tests for ShutdownOrchestrator

Tests the shutdown orchestration logic including success/failure handling,
statistics collection, and logging behavior.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.shutdown_orchestrator import ShutdownOrchestrator
from src.models import InstanceInfo, ShutdownResult


class TestShutdownOrchestrator:
    """Test suite for ShutdownOrchestrator class"""
    
    def test_shutdown_empty_list(self):
        """Test shutdown with empty instance list"""
        # Arrange
        ec2_client = Mock()
        logger = Mock()
        orchestrator = ShutdownOrchestrator(ec2_client, logger)
        
        # Act
        result = orchestrator.shutdown_instances([])
        
        # Assert
        assert result.total_instances == 0
        assert result.successful_stops == 0
        assert result.failed_stops == 0
        assert result.errors == []
        ec2_client.stop_instance.assert_not_called()
    
    def test_shutdown_single_instance_success(self):
        """Test successful shutdown of single instance"""
        # Arrange
        ec2_client = Mock()
        ec2_client.stop_instance.return_value = True
        logger = Mock()
        orchestrator = ShutdownOrchestrator(ec2_client, logger)
        
        instances = [
            InstanceInfo(instance_id="i-123", instance_name="web-server", state="running")
        ]
        
        # Act
        result = orchestrator.shutdown_instances(instances)
        
        # Assert
        assert result.total_instances == 1
        assert result.successful_stops == 1
        assert result.failed_stops == 0
        assert result.errors == []
        ec2_client.stop_instance.assert_called_once_with("i-123")
        logger.info.assert_called_once()
        logger.error.assert_not_called()
    
    def test_shutdown_single_instance_failure(self):
        """Test failed shutdown of single instance"""
        # Arrange
        ec2_client = Mock()
        ec2_client.stop_instance.return_value = False
        logger = Mock()
        orchestrator = ShutdownOrchestrator(ec2_client, logger)
        
        instances = [
            InstanceInfo(instance_id="i-456", instance_name="db-server", state="running")
        ]
        
        # Act
        result = orchestrator.shutdown_instances(instances)
        
        # Assert
        assert result.total_instances == 1
        assert result.successful_stops == 0
        assert result.failed_stops == 1
        assert len(result.errors) == 1
        assert "i-456" in result.errors[0]
        assert "db-server" in result.errors[0]
        ec2_client.stop_instance.assert_called_once_with("i-456")
        logger.info.assert_not_called()
        logger.error.assert_called_once()
    
    def test_shutdown_multiple_instances_all_success(self):
        """Test successful shutdown of multiple instances"""
        # Arrange
        ec2_client = Mock()
        ec2_client.stop_instance.return_value = True
        logger = Mock()
        orchestrator = ShutdownOrchestrator(ec2_client, logger)
        
        instances = [
            InstanceInfo(instance_id="i-111", instance_name="web-1", state="running"),
            InstanceInfo(instance_id="i-222", instance_name="web-2", state="running"),
            InstanceInfo(instance_id="i-333", instance_name="web-3", state="running")
        ]
        
        # Act
        result = orchestrator.shutdown_instances(instances)
        
        # Assert
        assert result.total_instances == 3
        assert result.successful_stops == 3
        assert result.failed_stops == 0
        assert result.errors == []
        assert ec2_client.stop_instance.call_count == 3
        assert logger.info.call_count == 3
        logger.error.assert_not_called()
    
    def test_shutdown_multiple_instances_mixed_results(self):
        """Test shutdown with some successes and some failures"""
        # Arrange
        ec2_client = Mock()
        # First call succeeds, second fails, third succeeds
        ec2_client.stop_instance.side_effect = [True, False, True]
        logger = Mock()
        orchestrator = ShutdownOrchestrator(ec2_client, logger)
        
        instances = [
            InstanceInfo(instance_id="i-aaa", instance_name="server-1", state="running"),
            InstanceInfo(instance_id="i-bbb", instance_name="server-2", state="running"),
            InstanceInfo(instance_id="i-ccc", instance_name="server-3", state="running")
        ]
        
        # Act
        result = orchestrator.shutdown_instances(instances)
        
        # Assert
        assert result.total_instances == 3
        assert result.successful_stops == 2
        assert result.failed_stops == 1
        assert len(result.errors) == 1
        assert "i-bbb" in result.errors[0]
        assert ec2_client.stop_instance.call_count == 3
        assert logger.info.call_count == 2
        assert logger.error.call_count == 1
    
    def test_shutdown_continues_after_failure(self):
        """Test that processing continues even when individual stops fail"""
        # Arrange
        ec2_client = Mock()
        # First two fail, third succeeds
        ec2_client.stop_instance.side_effect = [False, False, True]
        logger = Mock()
        orchestrator = ShutdownOrchestrator(ec2_client, logger)
        
        instances = [
            InstanceInfo(instance_id="i-fail1", instance_name="fail-1", state="running"),
            InstanceInfo(instance_id="i-fail2", instance_name="fail-2", state="running"),
            InstanceInfo(instance_id="i-success", instance_name="success", state="running")
        ]
        
        # Act
        result = orchestrator.shutdown_instances(instances)
        
        # Assert
        assert result.total_instances == 3
        assert result.successful_stops == 1
        assert result.failed_stops == 2
        assert len(result.errors) == 2
        # Verify all three instances were attempted
        assert ec2_client.stop_instance.call_count == 3
    
    def test_shutdown_logs_instance_details(self):
        """Test that instance details are logged correctly"""
        # Arrange
        ec2_client = Mock()
        ec2_client.stop_instance.return_value = True
        logger = Mock()
        orchestrator = ShutdownOrchestrator(ec2_client, logger)
        
        instances = [
            InstanceInfo(instance_id="i-xyz", instance_name="test-server", state="running")
        ]
        
        # Act
        orchestrator.shutdown_instances(instances)
        
        # Assert
        logger.info.assert_called_once()
        call_args = logger.info.call_args
        assert "Successfully stopped instance" in call_args[0][0]
        assert call_args[1]["instance_id"] == "i-xyz"
        assert call_args[1]["instance_name"] == "test-server"
    
    def test_shutdown_instance_without_name(self):
        """Test shutdown of instance without a name tag"""
        # Arrange
        ec2_client = Mock()
        ec2_client.stop_instance.return_value = True
        logger = Mock()
        orchestrator = ShutdownOrchestrator(ec2_client, logger)
        
        instances = [
            InstanceInfo(instance_id="i-noname", instance_name="", state="running")
        ]
        
        # Act
        result = orchestrator.shutdown_instances(instances)
        
        # Assert
        assert result.successful_stops == 1
        logger.info.assert_called_once()
        call_args = logger.info.call_args
        assert call_args[1]["instance_id"] == "i-noname"
        assert call_args[1]["instance_name"] == ""
