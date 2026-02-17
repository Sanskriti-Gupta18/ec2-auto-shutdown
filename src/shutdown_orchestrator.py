"""
Shutdown Orchestrator for EC2 Auto-Shutdown Lambda

This module coordinates the shutdown of multiple EC2 instances,
collecting statistics and handling errors gracefully.
"""

from typing import List
from src.models import InstanceInfo, ShutdownResult
from src.ec2_client import EC2ClientWrapper
from src.logger import Logger


class ShutdownOrchestrator:
    """
    Coordinates the shutdown of multiple EC2 instances.
    
    This class manages the process of stopping multiple instances,
    collecting success/failure statistics, and logging each operation.
    Individual failures do not prevent other instances from being processed.
    """
    
    def __init__(self, ec2_client: EC2ClientWrapper, logger: Logger):
        """
        Initialize the orchestrator with EC2 client and logger.
        
        Args:
            ec2_client: EC2 client wrapper for stopping instances
            logger: Logger for recording operations
        """
        self.ec2_client = ec2_client
        self.logger = logger
    
    def shutdown_instances(self, instances: List[InstanceInfo]) -> ShutdownResult:
        """
        Stop all instances and return summary.
        
        This method iterates through all provided instances, attempts to stop each,
        and collects statistics. Processing continues even if individual stops fail.
        Each operation is logged with appropriate level (INFO for success, ERROR for failure).
        
        Args:
            instances: List of instances to stop
        
        Returns:
            ShutdownResult with statistics and error messages
        """
        total_instances = len(instances)
        successful_stops = 0
        failed_stops = 0
        errors = []
        
        for instance in instances:
            instance_id = instance.instance_id
            instance_name = instance.instance_name
            
            # Attempt to stop the instance
            success = self.ec2_client.stop_instance(instance_id)
            
            if success:
                successful_stops += 1
                # Log successful stop with instance details
                self.logger.info(
                    "Successfully stopped instance",
                    instance_id=instance_id,
                    instance_name=instance_name
                )
            else:
                failed_stops += 1
                error_msg = f"Failed to stop instance {instance_id}"
                if instance_name:
                    error_msg += f" ({instance_name})"
                errors.append(error_msg)
                
                # Log failure with instance details
                self.logger.error(
                    "Failed to stop instance",
                    instance_id=instance_id,
                    instance_name=instance_name
                )
        
        return ShutdownResult(
            total_instances=total_instances,
            successful_stops=successful_stops,
            failed_stops=failed_stops,
            errors=errors
        )
