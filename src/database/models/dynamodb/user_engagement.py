from datetime import datetime, timezone
from typing import Dict, Any, Optional
from decimal import Decimal
import uuid


class UserEngagement:
    """User engagement model for tracking detailed engagement history."""
    
    TABLE_NAME = "UserEngagement"
    
    @staticmethod
    def create_table(dynamodb):
        """Create the UserEngagement table in DynamoDB if it doesn't exist."""
        table = dynamodb.create_table(
            TableName=UserEngagement.TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'guild_id', 'KeyType': 'HASH'},     # Partition key
                {'AttributeName': 'engagement_id', 'KeyType': 'RANGE'} # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'guild_id', 'AttributeType': 'S'},
                {'AttributeName': 'engagement_id', 'AttributeType': 'S'},
                {'AttributeName': 'discord_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                {'AttributeName': 'activity_type', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIndex',
                    'KeySchema': [
                        {'AttributeName': 'discord_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                },
                {
                    'IndexName': 'ActivityTypeIndex',
                    'KeySchema': [
                        {'AttributeName': 'activity_type', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        return table
    
    def __init__(self,
                 guild_id: str,
                 discord_id: str,
                 activity_type: str,  # e.g., "message", "reaction", "match", "schedule"
                 engagement_id: Optional[str] = None,
                 timestamp: Optional[str] = None,  # ISO format with UTC timezone
                 details: Dict[str, Any] = None,
                 engagement_value: Decimal = None):
        """Initialize a UserEngagement instance."""
        self.guild_id = str(guild_id)
        self.discord_id = str(discord_id)
        self.activity_type = activity_type
        
        # Generate a unique ID if not provided (timestamp + random suffix)
        if engagement_id is None:
            now = datetime.now(timezone.utc)
            timestamp_str = now.strftime("%Y%m%d%H%M%S")
            random_suffix = str(uuid.uuid4())[:8]
            self.engagement_id = f"{timestamp_str}-{random_suffix}"
        else:
            self.engagement_id = engagement_id
            
        # Set timestamp to current time if not provided
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.details = details or {}
        self.engagement_value = engagement_value or Decimal('1.0')
    
    def to_dict(self) -> dict:
        """Convert engagement record to dictionary for DynamoDB storage."""
        return {
            "guild_id": self.guild_id,
            "discord_id": self.discord_id,
            "engagement_id": self.engagement_id,
            "timestamp": self.timestamp,
            "activity_type": self.activity_type,
            "details": self.details,
            "engagement_value": self.engagement_value
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'UserEngagement':
        """Create engagement instance from dictionary."""
        return UserEngagement(
            guild_id=data.get('guild_id'),
            discord_id=data.get('discord_id'),
            engagement_id=data.get('engagement_id'),
            timestamp=data.get('timestamp'),
            activity_type=data.get('activity_type'),
            details=data.get('details', {}),
            engagement_value=data.get('engagement_value')
        )
