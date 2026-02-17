"""
EC2 Client Wrapper for EC2 Auto-Shutdown Lambda

This module provides a resilient interface to EC2 API with retry logic
and pagination support for instance discovery and management.
"""

import time
from typing import List, Dict, Any, Callable, TypeVar
from functools import wraps
import boto3
from botocore.exceptions import ClientError

T = TypeVar('T')


def retry_with_exponential_backoff(max_retries: int, base_delay: float) -> Callable:
    """
    Decorator that implements exponential backoff retry logic for AWS API calls.
    
    This decorator retries operations that fail with throttling errors
    (RequestLimitExceeded) using exponential backoff. The delay between retries
    doubles with each attempt: base_delay, base_delay * 2, base_delay * 4, etc.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    
    Returns:
        Decorator function that wraps the target function with retry logic
    
    Example:
        @retry_with_exponential_backoff(max_retries=3, base_delay=1.0)
        def api_call():
            # This will retry up to 3 times with delays of 1s, 2s, 4s
            return client.some_operation()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    
                    # Only retry on throttling errors
                    if error_code == 'RequestLimitExceeded':
                        # If this is not the last attempt, sleep and retry
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            time.sleep(delay)
                            continue
                    
                    # Re-raise the error if it's not a throttling error
                    # or if we've exhausted all retries
                    raise
            
            # This should never be reached, but satisfies type checker
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class EC2ClientWrapper:
    """
    Wrapper for boto3 EC2 client with retry logic and pagination support.
    
    This class provides methods to interact with EC2 API for discovering
    and stopping instances, with built-in error handling and retry logic.
    """
    
    def __init__(self, region: str, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize EC2 client with retry configuration.
        
        Args:
            region: AWS region for EC2 operations
            max_retries: Maximum number of retry attempts for throttling errors
            base_delay: Base delay in seconds for exponential backoff
        """
        self.region = region
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.client = boto3.client('ec2', region_name=region)
    
    def describe_instances_by_tag(self, tag_key: str, tag_value: str) -> List[Dict[str, Any]]:
        """
        Query instances with specified tag using pagination.
        
        This method uses boto3 paginator to handle large result sets and
        returns all instances that match the specified tag key and value.
        Includes retry logic with exponential backoff for throttling errors.
        
        Args:
            tag_key: EC2 tag key to filter instances
            tag_value: EC2 tag value to filter instances
        
        Returns:
            List of instance dictionaries from EC2 API response
            
        Raises:
            ClientError: If EC2 API call fails (authentication, permissions, etc.)
        """
        @retry_with_exponential_backoff(self.max_retries, self.base_delay)
        def _describe_with_retry():
            instances = []
            
            # Create paginator for describe_instances
            paginator = self.client.get_paginator('describe_instances')
            
            # Define filter for tag
            filters = [
                {
                    'Name': f'tag:{tag_key}',
                    'Values': [tag_value]
                }
            ]
            
            # Paginate through results
            page_iterator = paginator.paginate(Filters=filters)
            
            for page in page_iterator:
                for reservation in page.get('Reservations', []):
                    instances.extend(reservation.get('Instances', []))
            
            return instances
        
        return _describe_with_retry()
    
    def stop_instance(self, instance_id: str) -> bool:
        """
        Stop a single instance with retry logic.
        
        This method attempts to stop an EC2 instance and returns success status.
        Includes exponential backoff retry logic for throttling errors.
        
        Args:
            instance_id: EC2 instance ID to stop
        
        Returns:
            True if instance stop was successful, False otherwise
        """
        @retry_with_exponential_backoff(self.max_retries, self.base_delay)
        def _stop_with_retry():
            return self.client.stop_instances(InstanceIds=[instance_id])
        
        try:
            _stop_with_retry()
            return True
        except ClientError as e:
            # Log error details but return False to allow continued processing
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            # Return False for all errors to allow continued processing
            return False
