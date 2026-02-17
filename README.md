# EC2 Auto-Shutdown Lambda

AWS Lambda function that automatically stops EC2 instances tagged with `AutoShutdown=yes`.

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   └── lambda_handler.py       # Main Lambda entry point
├── tests/
│   └── __init__.py
├── requirements.txt             # Python dependencies
└── README.md
```

## Dependencies

- **boto3**: AWS SDK for Python (EC2 API interactions)
- **hypothesis**: Property-based testing framework

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

The Lambda function is configured via environment variables:

- `TAG_KEY`: Tag key to filter instances (default: "AutoShutdown")
- `TAG_VALUE`: Tag value to filter instances (default: "yes")
- `MAX_RETRIES`: Maximum retry attempts for throttled API calls (default: 3)
- `AWS_REGION`: AWS region (automatically set by Lambda runtime)

## IAM Permissions Required

The Lambda execution role requires the following permissions:

- `ec2:DescribeInstances`
- `ec2:StopInstances`
- `ec2:DescribeInstanceStatus`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

## Testing

Run tests with:

```bash
python -m pytest tests/
```

## Deployment

Package and deploy using AWS SAM, Terraform, or the AWS Console.
