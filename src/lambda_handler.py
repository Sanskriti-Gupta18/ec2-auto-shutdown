"""
EC2 Auto-Shutdown Lambda Handler

This module provides the main entry point for the AWS Lambda function that
automatically shuts down EC2 instances based on tagging.
"""

from datetime import datetime
from typing import Any, Dict

from src.configuration import Configuration
from src.logger import Logger
from src.ec2_client import EC2ClientWrapper
from src.instance_discovery import InstanceDiscoveryService
from src.shutdown_orchestrator import ShutdownOrchestrator


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function for EC2 auto-shutdown.
    
    This function orchestrates the complete shutdown workflow:
    1. Loads configuration from environment variables
    2. Initializes all required components
    3. Discovers EC2 instances with the AutoShutdown tag
    4. Stops all discovered running instances
    5. Logs execution summary with statistics
    
    Args:
        event: Lambda event data (not currently used)
        context: Lambda context object (not currently used)
        
    Returns:
        Dictionary containing statusCode and execution summary with:
        - message: Human-readable status message
        - result: Statistics including total_instances, successful_stops, failed_stops
        
    Raises:
        Exception: Top-level exceptions are caught, logged, and returned as error responses
    """
    logger = None
    
    try:
        # Load configuration from environment variables
        config = Configuration.load()
        
        # Initialize Logger
        logger = Logger()
        
        # Log execution start with timestamp and region
        execution_start = datetime.utcnow().isoformat() + "Z"
        logger.info(
            "Starting EC2 auto-shutdown execution",
            timestamp=execution_start,
            region=config.region,
            tag_key=config.tag_key,
            tag_value=config.tag_value
        )
        
        # Initialize EC2ClientWrapper with configuration
        ec2_client = EC2ClientWrapper(
            region=config.region,
            max_retries=config.max_retries,
            base_delay=config.retry_base_delay
        )
        
        # Initialize InstanceDiscoveryService with EC2 client
        discovery_service = InstanceDiscoveryService(ec2_client)
        
        # Initialize ShutdownOrchestrator with EC2 client and logger
        orchestrator = ShutdownOrchestrator(ec2_client, logger)
        
        # Call discovery service to find instances
        instances = discovery_service.find_instances_to_stop(
            config.tag_key,
            config.tag_value
        )
        
        # Log count of discovered instances
        logger.info(
            "Instance discovery completed",
            instances_found=len(instances),
            tag_key=config.tag_key,
            tag_value=config.tag_value
        )
        
        # Call orchestrator to shutdown instances
        result = orchestrator.shutdown_instances(instances)
        
        # Log execution summary with statistics
        logger.info(
            "EC2 auto-shutdown execution completed",
            total_instances=result.total_instances,
            successful_stops=result.successful_stops,
            failed_stops=result.failed_stops,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        # Return structured response with execution summary
        return {
            "statusCode": 200,
            "body": {
                "message": "Shutdown operation completed",
                "result": {
                    "total_instances": result.total_instances,
                    "successful_stops": result.successful_stops,
                    "failed_stops": result.failed_stops
                }
            }
        }
        
    except Exception as e:
        # Handle top-level exceptions and log errors
        error_message = str(e)
        error_type = type(e).__name__
        
        # Log error if logger is available
        if logger:
            logger.error(
                "EC2 auto-shutdown execution failed",
                error_type=error_type,
                error_message=error_message,
                timestamp=datetime.utcnow().isoformat() + "Z"
            )
        
        # Return error response
        return {
            "statusCode": 500,
            "body": {
                "message": "Shutdown operation failed",
                "error": {
                    "type": error_type,
                    "message": error_message
                }
            }
        }
