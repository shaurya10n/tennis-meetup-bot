from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from decimal import Decimal

from src.database.models.dynamodb.user_engagement import UserEngagement


class UserEngagementDAO:
    """Data Access Object for UserEngagement model in DynamoDB."""
    
    def __init__(self, dynamodb):
        """Initialize UserEngagementDAO with DynamoDB resource."""
        self.table = dynamodb.Table(UserEngagement.TABLE_NAME)
    
    def create_engagement(self, guild_id: str, discord_id: str, activity_type: str,
                         details: Dict[str, Any] = None, 
                         engagement_value: float = 1.0) -> UserEngagement:
        """Create a new engagement record in the database.
        
        Args:
            guild_id: Discord server ID
            discord_id: Discord user ID
            activity_type: Type of activity (e.g., "message", "reaction", "match")
            details: Additional details about the engagement
            engagement_value: Value of the engagement for scoring
            
        Returns:
            UserEngagement: The created engagement object
        """
        # Convert engagement_value to Decimal for DynamoDB
        if isinstance(engagement_value, float):
            engagement_value = Decimal(str(engagement_value))
        
        engagement = UserEngagement(
            guild_id=guild_id,
            discord_id=discord_id,
            activity_type=activity_type,
            details=details,
            engagement_value=engagement_value
        )
        
        self.table.put_item(Item=engagement.to_dict())
        return engagement
    
    def get_engagement(self, guild_id: str, engagement_id: str) -> Optional[UserEngagement]:
        """Get an engagement record by Guild ID and engagement ID.
        
        Args:
            guild_id: Discord server ID
            engagement_id: Unique engagement ID
            
        Returns:
            Optional[UserEngagement]: The engagement object if found, None otherwise
        """
        response = self.table.get_item(Key={
            'guild_id': str(guild_id),
            'engagement_id': str(engagement_id)
        })
        item = response.get('Item')
        
        if not item:
            return None
            
        return UserEngagement.from_dict(item)
    
    def delete_engagement(self, guild_id: str, engagement_id: str) -> bool:
        """Delete an engagement record from the database.
        
        Args:
            guild_id: Discord server ID
            engagement_id: Unique engagement ID
            
        Returns:
            bool: True if engagement was deleted, False otherwise
        """
        response = self.table.delete_item(
            Key={
                'guild_id': str(guild_id),
                'engagement_id': str(engagement_id)
            },
            ReturnValues='ALL_OLD'
        )
        
        return 'Attributes' in response
    
    def list_engagements_by_user(self, guild_id: str, discord_id: str, 
                               start_time: str = None, end_time: str = None,
                               limit: int = 100) -> List[UserEngagement]:
        """List engagement records for a specific user in a guild.
        
        Args:
            guild_id: Discord server ID
            discord_id: Discord user ID
            start_time: Optional ISO timestamp to filter by start time
            end_time: Optional ISO timestamp to filter by end time
            limit: Maximum number of records to return
            
        Returns:
            List[UserEngagement]: List of engagement records
        """
        # Build filter expression for time range if provided
        filter_expressions = ["discord_id = :discord_id"]
        expression_values = {
            ":guild_id": str(guild_id),
            ":discord_id": str(discord_id)
        }
        
        if start_time:
            filter_expressions.append("timestamp >= :start_time")
            expression_values[":start_time"] = start_time
            
        if end_time:
            filter_expressions.append("timestamp <= :end_time")
            expression_values[":end_time"] = end_time
        
        filter_expression = " AND ".join(filter_expressions)
        
        # Query engagements for the user
        response = self.table.query(
            IndexName="UserIndex",
            KeyConditionExpression="discord_id = :discord_id",
            FilterExpression=f"guild_id = :guild_id" if guild_id else None,
            ExpressionAttributeValues=expression_values,
            Limit=limit
        )
        
        items = response.get('Items', [])
        engagements = [UserEngagement.from_dict(item) for item in items]
        return engagements
    
    def list_engagements_by_activity(self, guild_id: str, activity_type: str,
                                   start_time: str = None, end_time: str = None,
                                   limit: int = 100) -> List[UserEngagement]:
        """List engagement records for a specific activity type in a guild.
        
        Args:
            guild_id: Discord server ID
            activity_type: Type of activity (e.g., "message", "reaction", "match")
            start_time: Optional ISO timestamp to filter by start time
            end_time: Optional ISO timestamp to filter by end time
            limit: Maximum number of records to return
            
        Returns:
            List[UserEngagement]: List of engagement records
        """
        # Build filter expression for time range if provided
        filter_expressions = ["guild_id = :guild_id"]
        expression_values = {
            ":guild_id": str(guild_id),
            ":activity_type": activity_type
        }
        
        if start_time:
            filter_expressions.append("timestamp >= :start_time")
            expression_values[":start_time"] = start_time
            
        if end_time:
            filter_expressions.append("timestamp <= :end_time")
            expression_values[":end_time"] = end_time
        
        filter_expression = " AND ".join(filter_expressions)
        
        # Query engagements by activity type
        response = self.table.query(
            IndexName="ActivityTypeIndex",
            KeyConditionExpression="activity_type = :activity_type",
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_values,
            Limit=limit
        )
        
        items = response.get('Items', [])
        engagements = [UserEngagement.from_dict(item) for item in items]
        return engagements
    
    def calculate_user_engagement_score(self, guild_id: str, discord_id: str, 
                                      days: int = 30) -> Decimal:
        """Calculate a user's engagement score based on recent activity.
        
        Args:
            guild_id: Discord server ID
            discord_id: Discord user ID
            days: Number of days to include in calculation
            
        Returns:
            Decimal: The calculated engagement score
        """
        # Calculate the start time (N days ago)
        from datetime import timedelta
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        start_time = start_date.isoformat()
        
        # Get recent engagements
        engagements = self.list_engagements_by_user(
            guild_id=guild_id,
            discord_id=discord_id,
            start_time=start_time
        )
        
        # Calculate score as sum of engagement values
        score = sum(e.engagement_value for e in engagements)
        return score
