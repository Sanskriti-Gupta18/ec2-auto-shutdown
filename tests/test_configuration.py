"""
Unit tests for Configuration Manager

Tests configuration loading from environment variables with defaults.
"""

import os
import pytest
from src.configuration import Configuration


class TestConfiguration:
    """Test suite for Configuration class"""
    
    def test_load_with_defaults(self):
        """Test that default values are used when environment variables are missing"""
        # Set only required AWS_REGION
        os.environ['AWS_REGION'] = 'us-east-1'
        
        # Clear optional environment variables
        for key in ['TAG_KEY', 'TAG_VALUE', 'MAX_RETRIES', 'RETRY_BASE_DELAY']:
            os.environ.pop(key, None)
        
        config = Configuration.load()
        
        assert config.tag_key == 'AutoShutdown'
        assert config.tag_value == 'yes'
        assert config.region == 'us-east-1'
        assert config.max_retries == 3
        assert config.retry_base_delay == 1.0
    
    def test_load_with_custom_values(self):
        """Test that environment variables override defaults"""
        os.environ['TAG_KEY'] = 'CustomTag'
        os.environ['TAG_VALUE'] = 'custom-value'
        os.environ['AWS_REGION'] = 'eu-west-1'
        os.environ['MAX_RETRIES'] = '5'
        os.environ['RETRY_BASE_DELAY'] = '2.5'
        
        config = Configuration.load()
        
        assert config.tag_key == 'CustomTag'
        assert config.tag_value == 'custom-value'
        assert config.region == 'eu-west-1'
        assert config.max_retries == 5
        assert config.retry_base_delay == 2.5
    
    def test_load_missing_region_raises_error(self):
        """Test that missing AWS_REGION raises ValueError"""
        # Clear AWS_REGION
        os.environ.pop('AWS_REGION', None)
        
        with pytest.raises(ValueError, match="AWS_REGION environment variable must be set and not empty"):
            Configuration.load()
    
    def test_load_empty_region_raises_error(self):
        """Test that empty AWS_REGION raises ValueError"""
        os.environ['AWS_REGION'] = ''
        
        with pytest.raises(ValueError, match="AWS_REGION environment variable must be set and not empty"):
            Configuration.load()
    
    def test_region_from_aws_region_variable(self):
        """Test that region is loaded from AWS_REGION environment variable"""
        os.environ['AWS_REGION'] = 'ap-southeast-2'
        
        config = Configuration.load()
        
        assert config.region == 'ap-southeast-2'
