"""Unit tests for DynamoDB configuration."""

import os
from unittest.mock import patch

import pytest

from src.config import dynamodb_config


class TestDynamoDBConfig:
    def test_get_db_production(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            with patch("src.config.dynamodb_config.boto3.resource") as mock_resource:
                dynamodb_config.get_db()
                mock_resource.assert_called_once()

    def test_get_db_local_requires_endpoint(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("DYNAMODB_ENDPOINT", None)
                with pytest.raises(ValueError, match="DYNAMODB_ENDPOINT"):
                    dynamodb_config.get_db()

    def test_get_db_local_with_endpoint(self):
        env = {
            "ENVIRONMENT": "local",
            "DYNAMODB_ENDPOINT": "http://localhost:8000",
            "AWS_REGION": "us-west-2",
        }
        with patch.dict(os.environ, env, clear=False):
            with patch("src.config.dynamodb_config.boto3.resource") as mock_resource:
                dynamodb_config.get_db()
                mock_resource.assert_called_once_with(
                    "dynamodb",
                    endpoint_url="http://localhost:8000",
                    region_name="us-west-2",
                    aws_access_key_id="dummy",
                    aws_secret_access_key="dummy",
                )
