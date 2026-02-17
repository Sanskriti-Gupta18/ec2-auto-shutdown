# Requirements Document

## Introduction

This document specifies the requirements for an AWS Lambda function that automatically shuts down EC2 instances based on tagging. The system will identify EC2 instances tagged with `AutoShutdown=yes` and stop them, providing automated cost management and resource control.

## Glossary

- **Lambda_Function**: The AWS Lambda function that executes the shutdown logic
- **EC2_Instance**: An Amazon Elastic Compute Cloud virtual machine instance
- **AutoShutdown_Tag**: An EC2 instance tag with key "AutoShutdown" and value "yes"
- **EC2_API**: The AWS EC2 service API used for instance operations
- **CloudWatch_Logs**: AWS CloudWatch Logs service for storing execution logs

## Requirements

### Requirement 1: Instance Discovery

**User Story:** As a cloud administrator, I want the system to identify all EC2 instances with the AutoShutdown tag, so that only tagged instances are affected by automated shutdown.

#### Acceptance Criteria

1. WHEN the Lambda_Function executes, THE Lambda_Function SHALL query the EC2_API for all instances with the AutoShutdown_Tag
2. WHEN querying instances, THE Lambda_Function SHALL retrieve instances across all availability zones in the configured region
3. WHEN the EC2_API returns instances, THE Lambda_Function SHALL validate that each instance has the tag key "AutoShutdown" with value "yes"
4. WHEN no instances match the AutoShutdown_Tag, THE Lambda_Function SHALL log this condition and complete successfully

### Requirement 2: Instance Shutdown

**User Story:** As a cloud administrator, I want tagged instances to be stopped, so that I can reduce costs during non-business hours.

#### Acceptance Criteria

1. WHEN an EC2_Instance with the AutoShutdown_Tag is identified, THE Lambda_Function SHALL issue a stop command to the EC2_API for that instance
2. WHEN multiple instances are identified, THE Lambda_Function SHALL stop all identified instances
3. WHEN an instance is already in a stopped state, THE Lambda_Function SHALL skip that instance and continue processing
4. WHEN an instance is in a stopping state, THE Lambda_Function SHALL skip that instance and continue processing
5. WHEN an instance is successfully stopped, THE Lambda_Function SHALL log the instance ID and the action taken

### Requirement 3: Error Handling

**User Story:** As a cloud administrator, I want the system to handle errors gracefully, so that partial failures don't prevent other instances from being processed.

#### Acceptance Criteria

1. IF the EC2_API returns an authentication error, THEN THE Lambda_Function SHALL log the error with details and terminate execution
2. IF the EC2_API returns a permission error for a specific instance, THEN THE Lambda_Function SHALL log the error and continue processing remaining instances
3. IF the EC2_API returns a throttling error, THEN THE Lambda_Function SHALL implement exponential backoff retry logic up to 3 attempts
4. IF an instance stop operation fails, THEN THE Lambda_Function SHALL log the failure with instance ID and error details and continue processing remaining instances
5. IF the EC2_API is unavailable, THEN THE Lambda_Function SHALL log the error and terminate execution

### Requirement 4: Logging and Observability

**User Story:** As a cloud administrator, I want detailed execution logs, so that I can audit shutdown operations and troubleshoot issues.

#### Acceptance Criteria

1. WHEN the Lambda_Function starts execution, THE Lambda_Function SHALL log the execution start time and configured region
2. WHEN instances are discovered, THE Lambda_Function SHALL log the count of instances found with the AutoShutdown_Tag
3. WHEN an instance is stopped, THE Lambda_Function SHALL log the instance ID, instance name (if available), and timestamp
4. WHEN an error occurs, THE Lambda_Function SHALL log the error type, error message, and affected resource identifier
5. WHEN the Lambda_Function completes execution, THE Lambda_Function SHALL log a summary including total instances processed, successful stops, and failed stops
6. THE Lambda_Function SHALL write all logs to CloudWatch_Logs with appropriate log levels (INFO, WARN, ERROR)

### Requirement 5: AWS IAM Permissions

**User Story:** As a cloud administrator, I want the Lambda function to have appropriate IAM permissions, so that it can perform its operations securely with least privilege.

#### Acceptance Criteria

1. THE Lambda_Function SHALL require IAM permission `ec2:DescribeInstances` to query instances
2. THE Lambda_Function SHALL require IAM permission `ec2:StopInstances` to stop instances
3. THE Lambda_Function SHALL require IAM permission `ec2:DescribeInstanceStatus` to check instance states
4. THE Lambda_Function SHALL require IAM permission `logs:CreateLogGroup` to create CloudWatch log groups
5. THE Lambda_Function SHALL require IAM permission `logs:CreateLogStream` to create CloudWatch log streams
6. THE Lambda_Function SHALL require IAM permission `logs:PutLogEvents` to write log events

### Requirement 6: Configuration

**User Story:** As a cloud administrator, I want the Lambda function to be configurable, so that I can adjust its behavior without code changes.

#### Acceptance Criteria

1. THE Lambda_Function SHALL read the AWS region from the Lambda execution environment
2. WHERE a custom tag key is specified via environment variable, THE Lambda_Function SHALL use that tag key instead of "AutoShutdown"
3. WHERE a custom tag value is specified via environment variable, THE Lambda_Function SHALL use that tag value instead of "yes"
4. WHERE a retry count is specified via environment variable, THE Lambda_Function SHALL use that value for API retry attempts
5. WHEN environment variables are missing, THE Lambda_Function SHALL use default values ("AutoShutdown", "yes", 3 retries)
