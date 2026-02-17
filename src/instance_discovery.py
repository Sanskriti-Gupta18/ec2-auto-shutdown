"""
Instance Discovery Service for EC2 Auto-Shutdown Lambda

This module provides functionality to discover and filter EC2 instances
that should be stopped based on tags and instance state.
"""

from typing import List
from src.ec2_client import EC2ClientWrapper
from src.models import InstanceInfo


class InstanceDiscoveryService:
    """
    Service for discovering EC2 instances that should be stopped.
    
    This class queries EC2 for instances with specific tags and filters
    them to only include instances in stoppable states (currently "running").
    """
    
    def __init__(self, ec2_client: EC2ClientWrapper):
        """
        Initialize the discovery service with an EC2 client wrapper.
        
        Args:
            ec2_client: EC2ClientWrapper instance for making API calls
        """
        self.ec2_client = ec2_client
    
    def find_instances_to_stop(self, tag_key: str, tag_value: str) -> List[InstanceInfo]:
        """
        Find all instances with specified tag that are in stoppable states.
        
        This method queries EC2 for instances with the specified tag and filters
        them to only include instances in "running" state. Instances in "stopped",
        "stopping", "terminated", or "terminating" states are excluded.
        
        Args:
            tag_key: EC2 tag key to filter instances (e.g., "AutoShutdown")
            tag_value: EC2 tag value to filter instances (e.g., "yes")
        
        Returns:
            List of InstanceInfo objects for instances that should be stopped
        """
        # Query EC2 for instances with the specified tag
        instances = self.ec2_client.describe_instances_by_tag(tag_key, tag_value)
        
        # Filter and transform instances
        instances_to_stop = []
        
        for instance in instances:
            # Get instance state
            state = instance.get('State', {}).get('Name', '')
            
            # Only include instances in "running" state
            if state != 'running':
                continue
            
            # Extract instance ID
            instance_id = instance.get('InstanceId', '')
            
            # Extract instance name from 'Name' tag if present
            instance_name = ''
            tags = instance.get('Tags', [])
            for tag in tags:
                if tag.get('Key') == 'Name':
                    instance_name = tag.get('Value', '')
                    break
            
            # Create InstanceInfo object
            instance_info = InstanceInfo(
                instance_id=instance_id,
                instance_name=instance_name,
                state=state
            )
            
            instances_to_stop.append(instance_info)
        
        return instances_to_stop
