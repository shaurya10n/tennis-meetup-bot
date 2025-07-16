import os
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_db():
    """
    Get DynamoDB resource based on environment
    """
    # Default to production for safety
    environment = os.getenv("ENVIRONMENT", "production").lower()

    if environment in ["development", "local"]:
        # Local development using DynamoDB Local
        print("Connecting to local DynamoDB instance...")
        endpoint_url = os.getenv("DYNAMODB_ENDPOINT")
        if not endpoint_url:
            raise ValueError("DYNAMODB_ENDPOINT must be set for local development.")
        return boto3.resource('dynamodb',
            endpoint_url=endpoint_url,
            region_name=os.getenv("AWS_REGION", "us-west-2"),
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy')
    else:
        # Production environment - use AWS credentials and AWS DynamoDB
        print("Connecting to AWS DynamoDB...")
        return boto3.resource('dynamodb',
            region_name=os.getenv("AWS_REGION", "us-west-2"))
