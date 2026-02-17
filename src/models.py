"""
Data Models for EC2 Auto-Shutdown Lambda

This module defines data classes used throughout the EC2 auto-shutdown
Lambda function for representing instance information and operation results.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class InstanceInfo:
    """
    Information about an EC2 instance.
    
    This class represents the essential information about an EC2 instance
    needed for the auto-shutdown process.
    
    Attributes:
        instance_id: EC2 instance ID (e.g., "i-1234567890abcdef0")
        instance_name: Instance name from 'Name' tag, or empty string if not present
        state: Current instance state (e.g., "running", "stopped", "stopping")
    """
    instance_id: str
    instance_name: str
    state: str


@dataclass
class ShutdownResult:
    """
    Result of a shutdown operation.
    
    This class represents the outcome of attempting to stop multiple EC2 instances,
    including statistics and error information for audit and logging purposes.
    
    Attributes:
        total_instances: Total number of instances processed
        successful_stops: Number of instances successfully stopped
        failed_stops: Number of instances that failed to stop
        errors: List of error messages for failed stop operations
    """
    total_instances: int
    successful_stops: int
    failed_stops: int
    errors: List[str]
