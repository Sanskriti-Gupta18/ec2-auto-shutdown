# Implementation Plan: EC2 Auto-Shutdown Lambda

## Overview

This implementation plan breaks down the EC2 Auto-Shutdown Lambda function into discrete coding tasks. The approach follows an incremental development pattern: configuration and infrastructure first, core components next, then integration, and finally comprehensive testing. Each task builds on previous work to ensure continuous validation.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create directory structure for Lambda function
  - Create `requirements.txt` with boto3 and hypothesis dependencies
  - Create basic Lambda handler entry point file
  - Set up logging configuration
  - _Requirements: 4.6_

- [ ] 2. Implement Configuration Manager
  - [x] 2.1 Create Configuration class with environment variable loading
    - Implement `Configuration` class with fields for tag_key, tag_value, region, max_retries, retry_base_delay
    - Implement `load()` static method to read from environment variables with defaults
    - Add validation for required fields (region must not be empty)
    - _Requirements: 6.1, 6.5_
  
  - [ ]* 2.2 Write property test for configuration overrides
    - **Property 13: Environment variable overrides are respected**
    - **Validates: Requirements 6.2, 6.3, 6.4**
  
  - [ ]* 2.3 Write unit tests for configuration defaults
    - Test default values when environment variables are missing
    - Test region loading from AWS_REGION
    - _Requirements: 6.1, 6.5_

- [ ] 3. Implement EC2 Client Wrapper with retry logic
  - [x] 3.1 Create EC2ClientWrapper class
    - Initialize boto3 EC2 client with region
    - Implement `describe_instances_by_tag()` method using paginator
    - Implement `stop_instance()` method with basic error handling
    - _Requirements: 1.1, 1.2, 2.1_
  
  - [x] 3.2 Add exponential backoff retry logic
    - Implement retry decorator with exponential backoff
    - Handle throttling errors (RequestLimitExceeded)
    - Apply retry logic to EC2 API calls
    - _Requirements: 3.3_
  
  - [ ]* 3.3 Write property test for throttling retry behavior
    - **Property 6: Throttling triggers exponential backoff retry**
    - **Validates: Requirements 3.3**
  
  - [ ]* 3.4 Write unit tests for EC2 client error handling
    - Test authentication errors terminate execution
    - Test API unavailable errors terminate execution
    - _Requirements: 3.1, 3.5_

- [x] 4. Checkpoint - Ensure configuration and EC2 client tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement Instance Discovery Service
  - [x] 5.1 Create InstanceInfo data class
    - Define InstanceInfo with instance_id, instance_name, state fields
    - _Requirements: 1.3_
  
  - [x] 5.2 Create InstanceDiscoveryService class
    - Implement `find_instances_to_stop()` method
    - Query EC2 using client wrapper with tag filters
    - Extract instance information from EC2 response
    - Filter to only include instances in "running" state
    - Extract instance name from 'Name' tag if present
    - _Requirements: 1.1, 1.2, 1.3, 2.3, 2.4_
  
  - [ ]* 5.3 Write property test for tag-based discovery
    - **Property 1: Tag-based instance discovery**
    - **Validates: Requirements 1.1, 1.3**
  
  - [ ]* 5.4 Write property test for state filtering
    - **Property 3: Non-running instances are excluded**
    - **Validates: Requirements 2.3, 2.4**
  
  - [ ]* 5.5 Write unit test for empty instance list
    - Test behavior when no instances match the tag
    - _Requirements: 1.4_

- [ ] 6. Implement Logger with structured logging
  - [x] 6.1 Create Logger class
    - Implement info(), warning(), error() methods
    - Format messages with JSON structure for CloudWatch Logs Insights
    - Include timestamp, log level, and message in all logs
    - Support additional structured fields via kwargs
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [ ]* 6.2 Write property test for log level assignment
    - **Property 12: Log levels are appropriate for message types**
    - **Validates: Requirements 4.6**
  
  - [ ]* 6.3 Write property test for error logging structure
    - **Property 10: Errors are logged with structured information**
    - **Validates: Requirements 4.4**

- [ ] 7. Implement Shutdown Orchestrator
  - [x] 7.1 Create ShutdownResult data class
    - Define ShutdownResult with total_instances, successful_stops, failed_stops, errors fields
    - _Requirements: 4.5_
  
  - [x] 7.2 Create ShutdownOrchestrator class
    - Implement `shutdown_instances()` method
    - Iterate through all instances and call EC2 client to stop each
    - Collect success/failure statistics
    - Log each operation with appropriate level
    - Continue processing even if individual stops fail
    - _Requirements: 2.1, 2.2, 2.5, 3.2, 3.4_
  
  - [ ]* 7.3 Write property test for all instances processed
    - **Property 2: All tagged running instances receive stop commands**
    - **Validates: Requirements 2.1, 2.2**
  
  - [ ]* 7.4 Write property test for error isolation
    - **Property 5: Individual failures don't prevent other instances from processing**
    - **Validates: Requirements 3.2, 3.4**
  
  - [ ]* 7.5 Write property test for successful stop logging
    - **Property 4: Successful stops are logged with instance details**
    - **Validates: Requirements 2.5**

- [x] 8. Checkpoint - Ensure core component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement Lambda handler and integrate components
  - [x] 9.1 Implement lambda_handler function
    - Load configuration using Configuration.load()
    - Initialize Logger
    - Initialize EC2ClientWrapper with configuration
    - Initialize InstanceDiscoveryService with EC2 client
    - Initialize ShutdownOrchestrator with EC2 client and logger
    - Log execution start with timestamp and region
    - Call discovery service to find instances
    - Log count of discovered instances
    - Call orchestrator to shutdown instances
    - Log execution summary with statistics
    - Handle top-level exceptions and log errors
    - Return structured response with execution summary
    - _Requirements: 1.1, 1.4, 2.1, 2.2, 4.1, 4.2, 4.5_
  
  - [ ]* 9.2 Write property test for execution start logging
    - **Property 7: Execution start is logged with configuration**
    - **Validates: Requirements 4.1**
  
  - [ ]* 9.3 Write property test for discovery count logging
    - **Property 8: Instance discovery count is logged**
    - **Validates: Requirements 4.2**
  
  - [ ]* 9.4 Write property test for instance stop detail logging
    - **Property 9: Instance stops are logged with full details**
    - **Validates: Requirements 4.3**
  
  - [ ]* 9.5 Write property test for execution summary logging
    - **Property 11: Execution summary is logged at completion**
    - **Validates: Requirements 4.5**

- [ ] 10. Create IAM policy document
  - [x] 10.1 Create IAM policy JSON file
    - Define policy with required EC2 permissions (DescribeInstances, StopInstances, DescribeInstanceStatus)
    - Define policy with required CloudWatch Logs permissions (CreateLogGroup, CreateLogStream, PutLogEvents)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ]* 11. Write integration tests
  - [ ]* 11.1 Write integration test with mocked AWS services
    - Test complete Lambda handler execution with mocked boto3 responses
    - Verify end-to-end flow from discovery to shutdown
    - Test with various instance configurations
    - _Requirements: 1.1, 2.1, 2.2, 4.5_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Run complete test suite
  - Verify all property tests pass with 100+ iterations
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases
- The implementation uses Python with boto3 for AWS SDK
- Hypothesis library is used for property-based testing
