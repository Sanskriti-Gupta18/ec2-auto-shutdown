"""
Configuration Manager for EC2 Auto-Shutdown Lambda

This module provides configuration loading from environment variables with
sensible defaults for the EC2 auto-shutdown Lambda function.
"""

import os
from dataclasses import dataclass


@dataclass
class Configuration:
    """
    Configuration for EC2 Auto-Shutdown Lambda function.
    
    Attributes:
        tag_key: EC2 tag key to filter instances (default: "AutoShutdown")
        tag_value: EC2 tag value to filter instances (default: "yes")
        region: AWS region for EC2 operations (required)
        max_retries: Maximum number of retry attempts for API calls (default: 3)
        retry_base_delay: Base delay in seconds for exponential backoff (default: 1.0)
    """
    tag_key: str
    tag_value: str
    region: str
    max_retries: int
    retry_base_delay: float
    
    @staticmethod
    def load() -> 'Configuration':
        """
        Load configuration from environment variables with defaults.
        
        Environment Variables:
            TAG_KEY: Custom tag key (default: "AutoShutdown")
            TAG_VALUE: Custom tag value (default: "yes")
            AWS_REGION: AWS region (required, no default)
            MAX_RETRIES: Maximum retry attempts (default: "3")
            RETRY_BASE_DELAY: Base delay for retries in seconds (default: "1.0")
        
        Returns:
            Configuration instance with loaded values
            
        Raises:
            ValueError: If region is empty or not set
        """
        # Load configuration from environment variables with defaults
        tag_key = os.environ.get('TAG_KEY', 'AutoShutdown')
        tag_value = os.environ.get('TAG_VALUE', 'yes')
        region = os.environ.get('AWS_REGION', '')
        max_retries = int(os.environ.get('MAX_RETRIES', '3'))
        retry_base_delay = float(os.environ.get('RETRY_BASE_DELAY', '1.0'))
        
        # Validate required fields
        if not region:
            raise ValueError("AWS_REGION environment variable must be set and not empty")
        
        return Configuration(
            tag_key=tag_key,
            tag_value=tag_value,
            region=region,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay
        )
