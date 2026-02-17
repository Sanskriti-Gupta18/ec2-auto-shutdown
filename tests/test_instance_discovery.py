"""
Unit tests for InstanceDiscoveryService

Tests the instance discovery functionality including filtering by state
and extracting instance information from EC2 responses.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.instance_discovery import InstanceDiscoveryService
from src.ec2_client import EC2ClientWrapper
from src.models import InstanceInfo


@pytest.fixture
def mock_ec2_client():
    """Create a mock EC2ClientWrapper for testing."""
    return Mock(spec=EC2ClientWrapper)


def test_find_instances_to_stop_running_instances(mock_ec2_client):
    """Test find_instances_to_stop returns only running instances."""
    # Mock EC2 response with running instances
    mock_ec2_client.describe_instances_by_tag.return_value = [
        {
            'InstanceId': 'i-111',
            'State': {'Name': 'running'},
            'Tags': [
                {'Key': 'Name', 'Value': 'web-server-01'},
                {'Key': 'AutoShutdown', 'Value': 'yes'}
            ]
        },
        {
            'InstanceId': 'i-222',
            'State': {'Name': 'running'},
            'Tags': [
                {'Key': 'Name', 'Value': 'app-server-01'},
                {'Key': 'AutoShutdown', 'Value': 'yes'}
            ]
        }
    ]
    
    service = InstanceDiscoveryService(mock_ec2_client)
    instances = service.find_instances_to_stop('AutoShutdown', 'yes')
    
    assert len(instances) == 2
    assert instances[0].instance_id == 'i-111'
    assert instances[0].instance_name == 'web-server-01'
    assert instances[0].state == 'running'
    assert instances[1].instance_id == 'i-222'
    assert instances[1].instance_name == 'app-server-01'
    assert instances[1].state == 'running'
    
    mock_ec2_client.describe_instances_by_tag.assert_called_once_with('AutoShutdown', 'yes')


def test_find_instances_to_stop_filters_stopped_instances(mock_ec2_client):
    """Test find_instances_to_stop excludes stopped instances."""
    mock_ec2_client.describe_instances_by_tag.return_value = [
        {
            'InstanceId': 'i-111',
            'State': {'Name': 'running'},
            'Tags': [{'Key': 'Name', 'Value': 'running-instance'}]
        },
        {
            'InstanceId': 'i-222',
            'State': {'Name': 'stopped'},
            'Tags': [{'Key': 'Name', 'Value': 'stopped-instance'}]
        }
    ]
    
    service = InstanceDiscoveryService(mock_ec2_client)
    instances = service.find_instances_to_stop('AutoShutdown', 'yes')
    
    assert len(instances) == 1
    assert instances[0].instance_id == 'i-111'
    assert instances[0].state == 'running'


def test_find_instances_to_stop_filters_stopping_instances(mock_ec2_client):
    """Test find_instances_to_stop excludes stopping instances."""
    mock_ec2_client.describe_instances_by_tag.return_value = [
        {
            'InstanceId': 'i-111',
            'State': {'Name': 'running'},
            'Tags': []
        },
        {
            'InstanceId': 'i-222',
            'State': {'Name': 'stopping'},
            'Tags': []
        }
    ]
    
    service = InstanceDiscoveryService(mock_ec2_client)
    instances = service.find_instances_to_stop('AutoShutdown', 'yes')
    
    assert len(instances) == 1
    assert instances[0].instance_id == 'i-111'


def test_find_instances_to_stop_filters_terminated_instances(mock_ec2_client):
    """Test find_instances_to_stop excludes terminated instances."""
    mock_ec2_client.describe_instances_by_tag.return_value = [
        {
            'InstanceId': 'i-111',
            'State': {'Name': 'running'},
            'Tags': []
        },
        {
            'InstanceId': 'i-222',
            'State': {'Name': 'terminated'},
            'Tags': []
        }
    ]
    
    service = InstanceDiscoveryService(mock_ec2_client)
    instances = service.find_instances_to_stop('AutoShutdown', 'yes')
    
    assert len(instances) == 1
    assert instances[0].instance_id == 'i-111'


def test_find_instances_to_stop_filters_terminating_instances(mock_ec2_client):
    """Test find_instances_to_stop excludes terminating instances."""
    mock_ec2_client.describe_instances_by_tag.return_value = [
        {
            'InstanceId': 'i-111',
            'State': {'Name': 'running'},
            'Tags': []
        },
        {
            'InstanceId': 'i-222',
            'State': {'Name': 'terminating'},
            'Tags': []
        }
    ]
    
    service = InstanceDiscoveryService(mock_ec2_client)
    instances = service.find_instances_to_stop('AutoShutdown', 'yes')
    
    assert len(instances) == 1
    assert instances[0].instance_id == 'i-111'


def test_find_instances_to_stop_empty_results(mock_ec2_client):
    """Test find_instances_to_stop with no matching instances."""
    mock_ec2_client.describe_instances_by_tag.return_value = []
    
    service = InstanceDiscoveryService(mock_ec2_client)
    instances = service.find_instances_to_stop('AutoShutdown', 'yes')
    
    assert len(instances) == 0


def test_find_instances_to_stop_no_name_tag(mock_ec2_client):
    """Test find_instances_to_stop handles instances without Name tag."""
    mock_ec2_client.describe_instances_by_tag.return_value = [
        {
            'InstanceId': 'i-111',
            'State': {'Name': 'running'},
            'Tags': [
                {'Key': 'AutoShutdown', 'Value': 'yes'},
                {'Key': 'Environment', 'Value': 'production'}
            ]
        }
    ]
    
    service = InstanceDiscoveryService(mock_ec2_client)
    instances = service.find_instances_to_stop('AutoShutdown', 'yes')
    
    assert len(instances) == 1
    assert instances[0].instance_id == 'i-111'
    assert instances[0].instance_name == ''  # Empty string when no Name tag
    assert instances[0].state == 'running'


def test_find_instances_to_stop_no_tags(mock_ec2_client):
    """Test find_instances_to_stop handles instances with no tags."""
    mock_ec2_client.describe_instances_by_tag.return_value = [
        {
            'InstanceId': 'i-111',
            'State': {'Name': 'running'},
            'Tags': []
        }
    ]
    
    service = InstanceDiscoveryService(mock_ec2_client)
    instances = service.find_instances_to_stop('AutoShutdown', 'yes')
    
    assert len(instances) == 1
    assert instances[0].instance_id == 'i-111'
    assert instances[0].instance_name == ''
    assert instances[0].state == 'running'


def test_find_instances_to_stop_mixed_states(mock_ec2_client):
    """Test find_instances_to_stop with instances in various states."""
    mock_ec2_client.describe_instances_by_tag.return_value = [
        {
            'InstanceId': 'i-111',
            'State': {'Name': 'running'},
            'Tags': [{'Key': 'Name', 'Value': 'instance-1'}]
        },
        {
            'InstanceId': 'i-222',
            'State': {'Name': 'stopped'},
            'Tags': [{'Key': 'Name', 'Value': 'instance-2'}]
        },
        {
            'InstanceId': 'i-333',
            'State': {'Name': 'running'},
            'Tags': [{'Key': 'Name', 'Value': 'instance-3'}]
        },
        {
            'InstanceId': 'i-444',
            'State': {'Name': 'stopping'},
            'Tags': [{'Key': 'Name', 'Value': 'instance-4'}]
        },
        {
            'InstanceId': 'i-555',
            'State': {'Name': 'running'},
            'Tags': [{'Key': 'Name', 'Value': 'instance-5'}]
        }
    ]
    
    service = InstanceDiscoveryService(mock_ec2_client)
    instances = service.find_instances_to_stop('AutoShutdown', 'yes')
    
    # Should only return the 3 running instances
    assert len(instances) == 3
    assert instances[0].instance_id == 'i-111'
    assert instances[1].instance_id == 'i-333'
    assert instances[2].instance_id == 'i-555'
    assert all(inst.state == 'running' for inst in instances)


def test_find_instances_to_stop_custom_tag(mock_ec2_client):
    """Test find_instances_to_stop with custom tag key and value."""
    mock_ec2_client.describe_instances_by_tag.return_value = [
        {
            'InstanceId': 'i-111',
            'State': {'Name': 'running'},
            'Tags': [
                {'Key': 'Name', 'Value': 'custom-instance'},
                {'Key': 'Environment', 'Value': 'dev'}
            ]
        }
    ]
    
    service = InstanceDiscoveryService(mock_ec2_client)
    instances = service.find_instances_to_stop('Environment', 'dev')
    
    assert len(instances) == 1
    assert instances[0].instance_id == 'i-111'
    
    mock_ec2_client.describe_instances_by_tag.assert_called_once_with('Environment', 'dev')
