import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal


class Match:
    """Match model for DynamoDB representing a tennis match between players."""
    
    TABLE_NAME = "Matches"
    
    @staticmethod
    def create_table(dynamodb):
        """Create the Matches table in DynamoDB if it doesn't exist."""
        table = dynamodb.create_table(
            TableName=Match.TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'guild_id', 'KeyType': 'HASH'},     # Partition key
                {'AttributeName': 'match_id', 'KeyType': 'RANGE'}     # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'guild_id', 'AttributeType': 'S'},
                {'AttributeName': 'match_id', 'AttributeType': 'S'},
                {'AttributeName': 'schedule_id', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'},
                {'AttributeName': 'court_id', 'AttributeType': 'S'},
                {'AttributeName': 'start_time', 'AttributeType': 'N'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'ScheduleIndex',
                    'KeySchema': [
                        {'AttributeName': 'schedule_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'start_time', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                },
                {
                    'IndexName': 'CourtIndex',
                    'KeySchema': [
                        {'AttributeName': 'court_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'start_time', 'KeyType': 'RANGE'}
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
                 match_id: str = None,
                 schedule_id: str = None,
                 court_id: str = None,
                 start_time: int = None,  # Unix timestamp
                 end_time: int = None,    # Unix timestamp
                 players: List[str] = None,  # List of user_ids
                 match_type: str = "singles",  # singles, doubles
                 status: str = "scheduled",  # scheduled, in_progress, completed, cancelled
                 score: Optional[Dict[str, Any]] = None,
                 winner: Optional[str] = None,  # user_id of winner
                 match_quality_score: Optional[Decimal] = None,  # 0-10 rating of match quality
                 player_ratings: Optional[Dict[str, Decimal]] = None,  # NTRP ratings at time of match
                 created_at: Optional[str] = None,  # ISO format with UTC timezone
                 updated_at: Optional[str] = None,  # ISO format with UTC timezone
                 cancelled_reason: Optional[str] = None,
                 notes: Optional[str] = None):
        """Initialize a Match instance."""
        self.guild_id = str(guild_id)
        self.match_id = match_id or str(uuid.uuid4())
        self.schedule_id = schedule_id
        self.court_id = court_id
        self.start_time = start_time
        self.end_time = end_time
        self.players = players or []
        self.match_type = match_type
        self.status = status
        self.score = score or {}
        self.winner = winner
        self.match_quality_score = match_quality_score
        self.player_ratings = player_ratings or {}
        self.cancelled_reason = cancelled_reason
        self.notes = notes
        
        # Set timestamps with ISO format
        now_iso = datetime.now(timezone.utc).isoformat()
        self.created_at = created_at or now_iso
        self.updated_at = updated_at or now_iso
    
    def to_dict(self) -> dict:
        """Convert match to dictionary for DynamoDB storage."""
        data = {
            "guild_id": self.guild_id,
            "match_id": self.match_id,
            "players": self.players,
            "match_type": self.match_type,
            "status": self.status,
            "score": self.score,
            "player_ratings": self.player_ratings,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Only include these fields if they have values
        if self.schedule_id:
            data["schedule_id"] = self.schedule_id
        if self.court_id:
            data["court_id"] = self.court_id
        if self.start_time is not None:
            data["start_time"] = self.start_time
        if self.end_time is not None:
            data["end_time"] = self.end_time
        if self.winner:
            data["winner"] = self.winner
        if self.match_quality_score is not None:
            data["match_quality_score"] = self.match_quality_score
        if self.cancelled_reason:
            data["cancelled_reason"] = self.cancelled_reason
        if self.notes:
            data["notes"] = self.notes
            
        return data
    
    @staticmethod
    def from_dict(data: dict) -> 'Match':
        """Create match instance from dictionary."""
        # Convert timestamp fields to int if they exist
        start_time = data.get('start_time')
        if start_time is not None:
            start_time = int(start_time)
            
        end_time = data.get('end_time')
        if end_time is not None:
            end_time = int(end_time)
        
        return Match(
            guild_id=data.get('guild_id'),
            match_id=data.get('match_id'),
            schedule_id=data.get('schedule_id'),
            court_id=data.get('court_id'),
            start_time=start_time,
            end_time=end_time,
            players=data.get('players', []),
            match_type=data.get('match_type', 'singles'),
            status=data.get('status', 'scheduled'),
            score=data.get('score', {}),
            winner=data.get('winner'),
            match_quality_score=data.get('match_quality_score'),
            player_ratings=data.get('player_ratings', {}),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            cancelled_reason=data.get('cancelled_reason'),
            notes=data.get('notes')
        )
    
    def is_valid(self) -> Tuple[bool, str]:
        """Validate the match.
        
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        if not self.players:
            return False, "Match must have at least one player"
        
        if self.match_type == "singles" and len(self.players) != 2:
            return False, "Singles matches must have exactly 2 players"
        
        if self.match_type == "doubles" and len(self.players) != 4:
            return False, "Doubles matches must have exactly 4 players"
        
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            return False, "End time must be after start time"
        
        if self.status not in ["scheduled", "in_progress", "completed", "cancelled", "pending_confirmation"]:
            return False, "Invalid match status"
        
        return True, ""
    
    def get_duration_minutes(self) -> Optional[int]:
        """Get the duration of the match in minutes."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time) / 60)
        return None
    
    def add_player(self, user_id: str) -> bool:
        """Add a player to the match if there's room."""
        if self.match_type == "singles" and len(self.players) >= 2:
            return False
        if self.match_type == "doubles" and len(self.players) >= 4:
            return False
        
        if user_id not in self.players:
            self.players.append(user_id)
            return True
        return False
    
    def remove_player(self, user_id: str) -> bool:
        """Remove a player from the match."""
        if user_id in self.players:
            self.players.remove(user_id)
            return True
        return False
    
    def is_player_in_match(self, user_id: str) -> bool:
        """Check if a player is in this match."""
        return user_id in self.players
    
    def can_start(self) -> bool:
        """Check if the match can be started."""
        if self.status != "scheduled":
            return False
        
        if self.match_type == "singles" and len(self.players) != 2:
            return False
        
        if self.match_type == "doubles" and len(self.players) != 4:
            return False
        
        return True
    
    def start_match(self) -> bool:
        """Start the match."""
        if not self.can_start():
            return False
        
        self.status = "in_progress"
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return True
    
    def complete_match(self, winner: str, score: Dict[str, Any], quality_score: Optional[Decimal] = None) -> bool:
        """Complete the match with results."""
        if self.status != "in_progress":
            return False
        
        if winner not in self.players:
            return False
        
        self.status = "completed"
        self.winner = winner
        self.score = score
        self.match_quality_score = quality_score
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return True
    
    def cancel_match(self, reason: str = None) -> bool:
        """Cancel the match."""
        if self.status in ["completed", "cancelled"]:
            return False
        
        self.status = "cancelled"
        self.cancelled_reason = reason
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return True 