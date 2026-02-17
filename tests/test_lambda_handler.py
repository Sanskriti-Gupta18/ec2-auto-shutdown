"""
Unit tests for Lambda Handler

This module tests the main lambda_handler function to ensure proper
integration of all components and correct error handling.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.lambda_handler import lambda_handler
from src.models import InstanceInfo, ShutdownResult


class TestLambdaHandler:
    """Test suite for lambda_handler function."""
    
    @patch('src.lambda_handler.ShutdownOrchestrator')
    @patch('src.lambda_handler.InstanceDiscoveryService')
    @patch('src.lambda_handler.EC2ClientWrapper')
    @patch('src.lambda_handler.Logger')
    @patch('src.lambda_handler.Configuration')
    def test_lambda_handler_successful_execution(
        self,
        mock_config_class,
        mock_logger_class,
        mock_ec2_client_class,
        mock_discovery_class,
        mock_orchestrator_class
    ):
        """Test successful execution with instances found and stopped."""
        # Setup mock configuration
        mock_config = Mock()
        mock_config.region = 'us-east-1'
        mock_config.tag_key = 'AutoShutdown'
        mock_config.tag_value = 'yes'
        mock_config.max_retries = 3
        mock_config.retry_base_delay = 1.0
        mock_config_class.load.return_value = mock_config
        
        # Setup mock logger
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        
        # Setup mock EC2 client
        mock_ec2_client = Mock()
        mock_ec2_client_class.return_value = mock_ec2_client
        
        # Setup mock discovery service
        mock_discovery = Mock()
        mock_instances = [
            InstanceInfo(instance_id='i-123', instance_name='test-1', state='running'),
            InstanceInfo(instance_id='i-456', instance_name='test-2', state='running')
        ]
        mock_discovery.find_instances_to_stop.return_value = mock_instances
        mock_discovery_class.return_value = mock_discovery
        
        # Setup mock orchestrator
        mock_orchestrator = Mock()
        mock_result = ShutdownResult(
            total_instances=2,
            successful_stops=2,
            failed_stops=0,
            errors=[]
        )
        mock_orchestrator.shutdown_instances.return_value = mock_result
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Execute lambda handler
        response = lambda_handler({}, None)
        
        # Verify response
        assert response['statusCode'] == 200
        assert response['body']['message'] == 'Shutdown operation completed'
        assert response['body']['result']['total_instances'] == 2
        assert response['body']['result']['successful_stops'] == 2
        assert response['body']['result']['failed_stops'] == 0
        
        # Verify configuration was loaded
        mock_config_class.load.assert_called_once()
        
        # Verify logger was initialized and used
        mock_logger_class.assert_called_once()
        assert mock_logger.info.call_count >= 3  # Start, discovery, summary
        
        # Verify EC2 client was initialized with correct parameters
        mock_ec2_client_class.assert_called_once_with(
            region='us-east-1',
            max_retries=3,
            base_delay=1.0
        )
        
        # Verify discovery service was called
        mock_discovery.find_instances_to_stop.assert_called_once_with(
            'AutoShutdown',
            'yes'
        )
        
        # Verify orchestrator was called with discovered instances
        mock_orchestrator.shutdown_instances.assert_called_once_with(mock_instances)
    
    @patch('src.lambda_handler.ShutdownOrchestrator')
    @patch('src.lambda_handler.InstanceDiscoveryService')
    @patch('src.lambda_handler.EC2ClientWrapper')
    @patch('src.lambda_handler.Logger')
    @patch('src.lambda_handler.Configuration')
    def test_lambda_handler_no_instances_found(
        self,
        mock_config_class,
        mock_logger_class,
        mock_ec2_client_class,
        mock_discovery_class,
        mock_orchestrator_class
    ):
        """Test execution when no instances are found."""
        # Setup mock configuration
        mock_config = Mock()
        mock_config.region = 'us-west-2'
        mock_config.tag_key = 'AutoShutdown'
        mock_config.tag_value = 'yes'
        mock_config.max_retries = 3
        mock_config.retry_base_delay = 1.0
        mock_config_class.load.return_value = mock_config
        
        # Setup mock logger
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        
        # Setup mock EC2 client
        mock_ec2_client = Mock()
        mock_ec2_client_class.return_value = mock_ec2_client
        
        # Setup mock discovery service - no instances found
        mock_discovery = Mock()
        mock_discovery.find_instances_to_stop.return_value = []
        mock_discovery_class.return_value = mock_discovery
        
        # Setup mock orchestrator
        mock_orchestrator = Mock()
        mock_result = ShutdownResult(
            total_instances=0,
            successful_stops=0,
            failed_stops=0,
            errors=[]
        )
        mock_orchestrator.shutdown_instances.return_value = mock_result
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Execute lambda handler
        response = lambda_handler({}, None)
        
        # Verify response
        assert response['statusCode'] == 200
        assert response['body']['result']['total_instances'] == 0
        assert response['body']['result']['successful_stops'] == 0
        
        # Verify discovery logged zero instances
        info_calls = [call for call in mock_logger.info.call_args_list]
        discovery_log = [call for call in info_calls if 'Instance discovery completed' in str(call)]
        assert len(discovery_log) > 0
    
    @patch('src.lambda_handler.Logger')
    @patch('src.lambda_handler.Configuration')
    def test_lambda_handler_configuration_error(
        self,
        mock_config_class,
        mock_logger_class
    ):
        """Test error handling when configuration loading fails."""
        # Setup mock logger
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        
        # Setup configuration to raise error
        mock_config_class.load.side_effect = ValueError("AWS_REGION environment variable must be set and not empty")
        
        # Execute lambda handler
        response = lambda_handler({}, None)
        
        # Verify error response
        assert response['statusCode'] == 500
        assert response['body']['message'] == 'Shutdown operation failed'
        assert 'error' in response['body']
        assert response['body']['error']['type'] == 'ValueError'
        assert 'AWS_REGION' in response['body']['error']['message']
        
        # Logger is not initialized when configuration fails, so no error logging occurs
        # This is expected behavior - the error is still returned in the response
    
    @patch('src.lambda_handler.InstanceDiscoveryService')
    @patch('src.lambda_handler.EC2ClientWrapper')
    @patch('src.lambda_handler.Logger')
    @patch('src.lambda_handler.Configuration')
    def test_lambda_handler_discovery_error(
        self,
        mock_config_class,
        mock_logger_class,
        mock_ec2_client_class,
        mock_discovery_class
    ):
        """Test error handling when instance discovery fails."""
        # Setup mock configuration
        mock_config = Mock()
        mock_config.region = 'us-east-1'
        mock_config.tag_key = 'AutoShutdown'
        mock_config.tag_value = 'yes'
        mock_config.max_retries = 3
        mock_config.retry_base_delay = 1.0
        mock_config_class.load.return_value = mock_config
        
        # Setup mock logger
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        
        # Setup mock EC2 client
        mock_ec2_client = Mock()
        mock_ec2_client_class.return_value = mock_ec2_client
        
        # Setup mock discovery service to raise error
        mock_discovery = Mock()
        mock_discovery.find_instances_to_stop.side_effect = Exception("EC2 API unavailable")
        mock_discovery_class.return_value = mock_discovery
        
        # Execute lambda handler
        response = lambda_handler({}, None)
        
        # Verify error response
        assert response['statusCode'] == 500
        assert response['body']['message'] == 'Shutdown operation failed'
        assert 'EC2 API unavailable' in response['body']['error']['message']
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
