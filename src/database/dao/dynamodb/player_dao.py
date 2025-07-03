from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from decimal import Decimal

from src.database.models.dynamodb.player import Player


class PlayerDAO:
    """Data Access Object for Player model in DynamoDB."""
    
    def __init__(self, dynamodb):
        """Initialize PlayerDAO with DynamoDB resource."""
        self.table = dynamodb.Table(Player.TABLE_NAME)
    
    def create_player(self, guild_id, user_id, username: str, 
                     dob: str, gender: str, ntrp_rating: float,
                     interests: List[str], knows_ntrp: bool, **kwargs) -> Player:
        """Create a new player in the database.
        
        Args:
            guild_id: Discord server ID
            user_id: Discord user ID
            username: Discord username
            dob: Date of birth (MM/DD/YYYY)
            gender: Player's gender
            ntrp_rating: NTRP rating (2.0-5.0)
            interests: List of tennis interests
            knows_ntrp: Whether user knew their NTRP rating
            **kwargs: Additional player attributes
            
        Returns:
            Player: The created player object
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Convert ntrp_rating to Decimal for DynamoDB
        if isinstance(ntrp_rating, float):
            ntrp_rating = Decimal(str(ntrp_rating))
        
        player = Player(
            guild_id=guild_id,
            user_id=user_id,
            username=username,
            dob=dob,
            gender=gender,
            ntrp_rating=ntrp_rating,
            interests=interests,
            knows_ntrp=knows_ntrp,
            created_at=now_iso,
            updated_at=now_iso,
            **kwargs
        )
        
        self.table.put_item(Item=player.to_dict())
        return player
    
    def get_player(self, guild_id, user_id) -> Optional[Player]:
        """Get a player by Guild ID and Discord ID.
        
        Args:
            guild_id: Discord server ID
            user_id: Discord user ID
            
        Returns:
            Optional[Player]: The player object if found, None otherwise
        """
        response = self.table.get_item(Key={
            'guild_id': str(guild_id),
            'user_id': str(user_id)
        })
        item = response.get('Item')
        
        if not item:
            return None
            
        return Player.from_dict(item)
    
    def update_player(self, guild_id, user_id, **update_data) -> Player:
        """Update a player's attributes.
        
        Args:
            guild_id: Discord server ID
            user_id: Discord user ID
            **update_data: Attributes to update
            
        Returns:
            Player: The updated player object
        """
        # Get current player data
        player = self.get_player(guild_id, user_id)
        if not player:
            raise ValueError(f"Player with guild_id {guild_id} and user_id {user_id} not found")
        
        # Update attributes
        update_expressions = []
        expression_values = {}
        expression_names = {}
        
        for key, value in update_data.items():
            update_expressions.append(f"#{key} = :{key}")
            expression_values[f":{key}"] = value
            expression_names[f"#{key}"] = key
        
        # Add updated_at timestamp
        now_iso = datetime.now(timezone.utc).isoformat()
        update_expressions.append("#updated_at = :updated_at")
        expression_values[":updated_at"] = now_iso
        expression_names["#updated_at"] = "updated_at"
        
        update_expression = "SET " + ", ".join(update_expressions)
        
        # Perform update
        self.table.update_item(
            Key={
                'guild_id': str(guild_id),
                'user_id': str(user_id)
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values
        )
        
        # Return updated player
        return self.get_player(guild_id, user_id)
