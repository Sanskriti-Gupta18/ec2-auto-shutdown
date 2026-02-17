"""
Unit tests for EC2ClientWrapper

Tests the EC2 client wrapper functionality including instance discovery
and stop operations with mocked boto3 responses.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from botocore.exceptions import ClientError
from src.ec2_client import EC2ClientWrapper, retry_with_exponential_backoff


@pytest.fixture
def mock_ec2_client():
    """Create a mock EC2 client for testing."""
    with patch('boto3.client') as mock_client:
        yield mock_client


def test_ec2_client_initialization(mock_ec2_client):
    """Test EC2ClientWrapper initializes with correct parameters."""
    wrapper = EC2ClientWrapper(region='us-east-1', max_retries=5, base_delay=2.0)
    
    assert wrapper.region == 'us-east-1'
    assert wrapper.max_retries == 5
    assert wrapper.base_delay == 2.0
    mock_ec2_client.assert_called_once_with('ec2', region_name='us-east-1')


def test_describe_instances_by_tag_single_page(mock_ec2_client):
    """Test describe_instances_by_tag with single page of results."""
    # Setup mock paginator
    mock_paginator = MagicMock()
    mock_ec2_instance = mock_ec2_client.return_value
    mock_ec2_instance.get_paginator.return_value = mock_paginator
    
    # Mock response with one page
    mock_paginator.paginate.return_value = [
        {
            'Reservations': [
                {
                    'Instances': [
                        {'InstanceId': 'i-123', 'State': {'Name': 'running'}},
                        {'InstanceId': 'i-456', 'State': {'Name': 'running'}}
                    ]
                }
            ]
        }
    ]
    
    wrapper = EC2ClientWrapper(region='us-east-1')
    instances = wrapper.describe_instances_by_tag('AutoShutdown', 'yes')
    
    assert len(instances) == 2
    assert instances[0]['InstanceId'] == 'i-123'
    assert instances[1]['InstanceId'] == 'i-456'
    
    # Verify paginator was called with correct filters
    mock_ec2_instance.get_paginator.assert_called_once_with('describe_instances')
    mock_paginator.paginate.assert_called_once()
    call_args = mock_paginator.paginate.call_args
    assert call_args[1]['Filters'][0]['Name'] == 'tag:AutoShutdown'
    assert call_args[1]['Filters'][0]['Values'] == ['yes']


def test_describe_instances_by_tag_multiple_pages(mock_ec2_client):
    """Test describe_instances_by_tag with multiple pages of results."""
    mock_paginator = MagicMock()
    mock_ec2_instance = mock_ec2_client.return_value
    mock_ec2_instance.get_paginator.return_value = mock_paginator
    
    # Mock response with multiple pages
    mock_paginator.paginate.return_value = [
        {
            'Reservations': [
                {'Instances': [{'InstanceId': 'i-111'}]}
            ]
        },
        {
            'Reservations': [
                {'Instances': [{'InstanceId': 'i-222'}]}
            ]
        },
        {
            'Reservations': [
                {'Instances': [{'InstanceId': 'i-333'}]}
            ]
        }
    ]
    
    wrapper = EC2ClientWrapper(region='us-west-2')
    instances = wrapper.describe_instances_by_tag('Environment', 'production')
    
    assert len(instances) == 3
    assert instances[0]['InstanceId'] == 'i-111'
    assert instances[1]['InstanceId'] == 'i-222'
    assert instances[2]['InstanceId'] == 'i-333'


def test_describe_instances_by_tag_empty_results(mock_ec2_client):
    """Test describe_instances_by_tag with no matching instances."""
    mock_paginator = MagicMock()
    mock_ec2_instance = mock_ec2_client.return_value
    mock_ec2_instance.get_paginator.return_value = mock_paginator
    
    # Mock empty response
    mock_paginator.paginate.return_value = [
        {'Reservations': []}
    ]
    
    wrapper = EC2ClientWrapper(region='eu-west-1')
    instances = wrapper.describe_instances_by_tag('AutoShutdown', 'yes')
    
    assert len(instances) == 0


def test_stop_instance_success(mock_ec2_client):
    """Test stop_instance with successful stop operation."""
    mock_ec2_instance = mock_ec2_client.return_value
    mock_ec2_instance.stop_instances.return_value = {
        'StoppingInstances': [
            {'InstanceId': 'i-123', 'CurrentState': {'Name': 'stopping'}}
        ]
    }
    
    wrapper = EC2ClientWrapper(region='us-east-1')
    result = wrapper.stop_instance('i-123')
    
    assert result is True
    mock_ec2_instance.stop_instances.assert_called_once_with(InstanceIds=['i-123'])


def test_stop_instance_client_error(mock_ec2_client):
    """Test stop_instance handles ClientError gracefully."""
    mock_ec2_instance = mock_ec2_client.return_value
    mock_ec2_instance.stop_instances.side_effect = ClientError(
        {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Not authorized'}},
        'StopInstances'
    )
    
    wrapper = EC2ClientWrapper(region='us-east-1')
    result = wrapper.stop_instance('i-123')
    
    assert result is False


def test_stop_instance_generic_error(mock_ec2_client):
    """Test stop_instance handles generic errors gracefully."""
    mock_ec2_instance = mock_ec2_client.return_value
    mock_ec2_instance.stop_instances.side_effect = ClientError(
        {'Error': {'Code': 'InternalError', 'Message': 'Internal server error'}},
        'StopInstances'
    )
    
    wrapper = EC2ClientWrapper(region='us-east-1')
    result = wrapper.stop_instance('i-999')
    
    assert result is False



def test_retry_decorator_success_on_first_attempt():
    """Test retry decorator succeeds on first attempt without retries."""
    call_count = 0
    
    @retry_with_exponential_backoff(max_retries=3, base_delay=0.1)
    def successful_operation():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = successful_operation()
    
    assert result == "success"
    assert call_count == 1


def test_retry_decorator_throttling_error_retries():
    """Test retry decorator retries on RequestLimitExceeded error."""
    call_count = 0
    
    @retry_with_exponential_backoff(max_retries=3, base_delay=0.01)
    def throttled_operation():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ClientError(
                {'Error': {'Code': 'RequestLimitExceeded', 'Message': 'Rate exceeded'}},
                'DescribeInstances'
            )
        return "success"
    
    start_time = time.time()
    result = throttled_operation()
    elapsed_time = time.time() - start_time
    
    assert result == "success"
    assert call_count == 3
    # Verify exponential backoff delays: 0.01s + 0.02s = 0.03s minimum
    assert elapsed_time >= 0.03


def test_retry_decorator_exhausts_retries():
    """Test retry decorator raises error after exhausting all retries."""
    call_count = 0
    
    @retry_with_exponential_backoff(max_retries=3, base_delay=0.01)
    def always_throttled():
        nonlocal call_count
        call_count += 1
        raise ClientError(
            {'Error': {'Code': 'RequestLimitExceeded', 'Message': 'Rate exceeded'}},
            'DescribeInstances'
        )
    
    with pytest.raises(ClientError) as exc_info:
        always_throttled()
    
    assert call_count == 3
    assert exc_info.value.response['Error']['Code'] == 'RequestLimitExceeded'


def test_retry_decorator_non_throttling_error_no_retry():
    """Test retry decorator does not retry non-throttling errors."""
    call_count = 0
    
    @retry_with_exponential_backoff(max_retries=3, base_delay=0.01)
    def auth_error_operation():
        nonlocal call_count
        call_count += 1
        raise ClientError(
            {'Error': {'Code': 'UnauthorizedOperation', 'Message': 'Not authorized'}},
            'StopInstances'
        )
    
    with pytest.raises(ClientError) as exc_info:
        auth_error_operation()
    
    assert call_count == 1  # Should not retry
    assert exc_info.value.response['Error']['Code'] == 'UnauthorizedOperation'


def test_describe_instances_with_throttling_retry(mock_ec2_client):
    """Test describe_instances_by_tag retries on throttling errors."""
    mock_paginator = MagicMock()
    mock_ec2_instance = mock_ec2_client.return_value
    mock_ec2_instance.get_paginator.return_value = mock_paginator
    
    call_count = 0
    
    def paginate_with_throttle(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ClientError(
                {'Error': {'Code': 'RequestLimitExceeded', 'Message': 'Rate exceeded'}},
                'DescribeInstances'
            )
        return [
            {
                'Reservations': [
                    {'Instances': [{'InstanceId': 'i-123'}]}
                ]
            }
        ]
    
    mock_paginator.paginate.side_effect = paginate_with_throttle
    
    wrapper = EC2ClientWrapper(region='us-east-1', max_retries=3, base_delay=0.01)
    instances = wrapper.describe_instances_by_tag('AutoShutdown', 'yes')
    
    assert len(instances) == 1
    assert instances[0]['InstanceId'] == 'i-123'
    assert call_count == 2


def test_stop_instance_with_throttling_retry(mock_ec2_client):
    """Test stop_instance retries on throttling errors."""
    mock_ec2_instance = mock_ec2_client.return_value
    
    call_count = 0
    
    def stop_with_throttle(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ClientError(
                {'Error': {'Code': 'RequestLimitExceeded', 'Message': 'Rate exceeded'}},
                'StopInstances'
            )
        return {'StoppingInstances': [{'InstanceId': 'i-123'}]}
    
    mock_ec2_instance.stop_instances.side_effect = stop_with_throttle
    
    wrapper = EC2ClientWrapper(region='us-east-1', max_retries=3, base_delay=0.01)
    result = wrapper.stop_instance('i-123')
    
    assert result is True
    assert call_count == 2
