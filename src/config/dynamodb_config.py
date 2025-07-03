import os
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_db():
    """
    Get DynamoDB resource based on environment
    """
    # Check if we're in local development or production
    is_local = os.getenv("ENVIRONMENT", "development") == "development"
    
    if is_local:
        # Local development using DynamoDB Local
        print("Connecting to local DynamoDB instance...")
        endpoint_url = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
        return boto3.resource('dynamodb',
            endpoint_url=endpoint_url,
            region_name=os.getenv("AWS_REGION", "us-west-2"),
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy')
    else:
        # Production environment - use AWS credentials
        print("Connecting to AWS DynamoDB...")
        return boto3.resource('dynamodb',
            region_name=os.getenv("AWS_REGION", "us-west-2"))
