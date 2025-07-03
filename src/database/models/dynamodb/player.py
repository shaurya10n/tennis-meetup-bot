import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal


class Player:
    """Player model for DynamoDB representing a tennis player in the system."""
    
    TABLE_NAME = "Players"
    
    @staticmethod
    def create_table(dynamodb):
        """Create the Players table in DynamoDB if it doesn't exist."""
        table = dynamodb.create_table(
            TableName=Player.TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'guild_id', 'KeyType': 'HASH'},     # Partition key
                {'AttributeName': 'user_id', 'KeyType': 'RANGE'}   # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'guild_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        return table
    
    def __init__(self, 
                 guild_id: str,               # Discord server ID
                 user_id: str,
                 username: str,
                 dob: str,                    # Format: "MM/DD/YYYY"
                 gender: str,
                 ntrp_rating: Decimal,
                 knows_ntrp: bool,
                 interests: List[str],
                 preferences: Dict[str, Any] = None,  # Map containing locations, skill_levels, gender
                 roles: List[Dict[str, str]] = None,  # List of maps with role_id and role_name
                 rating: Decimal = None,      # Algorithm-based rating (future)
                 rating_responses: Optional[Dict] = None,
                 calibration_ends_at: Optional[str] = None,  # ISO format with UTC timezone
                 last_rating_update: Optional[str] = None,   # ISO format with UTC timezone
                 created_at: Optional[str] = None,           # ISO format with UTC timezone
                 updated_at: Optional[str] = None,           # ISO format with UTC timezone
                 engagement_score: Optional[Decimal] = None,
                 last_active: Optional[str] = None,          # ISO format with UTC timezone
                 engagement_summary: Optional[Dict[str, Any]] = None):
        """Initialize a Player instance."""
        self.guild_id = str(guild_id)         # Convert to string for DynamoDB
        self.user_id = str(user_id)     # Convert to string for DynamoDB
        self.username = username
        self.dob = dob
        self.gender = gender
        self.ntrp_rating = ntrp_rating
        self.knows_ntrp = knows_ntrp
        self.interests = interests or []
        
        # Default preferences structure if not provided
        self.preferences = preferences or {
            "locations": [],
            "skill_levels": [],
            "gender": "none"
        }
        
        self.roles = roles or []
        self.rating = rating
        self.rating_responses = rating_responses
        
        # Set timestamps with ISO format
        now_iso = datetime.now(timezone.utc).isoformat()
        self.calibration_ends_at = calibration_ends_at
        self.last_rating_update = last_rating_update
        self.created_at = created_at or now_iso
        self.updated_at = updated_at or now_iso
        
        # Engagement metrics
        self.engagement_score = engagement_score or Decimal('0')
        self.last_active = last_active or now_iso
        self.engagement_summary = engagement_summary or {
            "total_matches_played": 0,
            "discord_messages_last_30_days": 0,
            "reaction_count": 0,
            "schedule_count": 0
        }
    
    def to_dict(self) -> dict:
        """Convert player to dictionary for DynamoDB storage."""
        return {
            "guild_id": self.guild_id,
            "user_id": self.user_id,
            "username": self.username,
            "dob": self.dob,
            "gender": self.gender,
            "ntrp_rating": self.ntrp_rating,
            "knows_ntrp": self.knows_ntrp,
            "interests": self.interests,
            "preferences": self.preferences,
            "roles": self.roles,
            "rating": self.rating,
            "rating_responses": self.rating_responses,
            "calibration_ends_at": self.calibration_ends_at,
            "last_rating_update": self.last_rating_update,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "engagement_score": self.engagement_score,
            "last_active": self.last_active,
            "engagement_summary": self.engagement_summary
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Player':
        """Create player instance from dictionary."""
        return Player(
            guild_id=data.get('guild_id'),
            user_id=data.get('user_id'),
            username=data.get('username'),
            dob=data.get('dob'),
            gender=data.get('gender'),
            ntrp_rating=data.get('ntrp_rating'),
            knows_ntrp=data.get('knows_ntrp', False),
            interests=data.get('interests', []),
            preferences=data.get('preferences', {
                "locations": [],
                "skill_levels": [],
                "gender": "none"
            }),
            roles=data.get('roles', []),
            rating=data.get('rating'),
            rating_responses=data.get('rating_responses'),
            calibration_ends_at=data.get('calibration_ends_at'),
            last_rating_update=data.get('last_rating_update'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            engagement_score=data.get('engagement_score'),
            last_active=data.get('last_active'),
            engagement_summary=data.get('engagement_summary', {
                "total_matches_played": 0,
                "discord_messages_last_30_days": 0,
                "reaction_count": 0,
                "schedule_count": 0
            })
        )
    
    def is_profile_complete(self) -> Tuple[bool, List[str]]:
        """Check if player profile is complete.

        Returns:
            tuple[bool, list[str]]: (is_complete, missing_fields)
            where missing_fields is a list of field names that need to be completed
        """
        missing_fields = []
        
        if not self.dob:
            missing_fields.append("date of birth")
        if not self.gender:
            missing_fields.append("gender")
        if self.ntrp_rating is None:
            missing_fields.append("NTRP rating")
        if not self.interests:
            missing_fields.append("tennis interests")
        if not self.preferences.get("locations"):
            missing_fields.append("preferred locations")
        if not self.preferences.get("skill_levels"):
            missing_fields.append("skill level preferences")
        if not self.preferences.get("gender"):
            missing_fields.append("gender preference")
            
        return (len(missing_fields) == 0, missing_fields)

    def can_update_rating(self) -> Tuple[bool, str]:
        """Check if player can update their NTRP rating.

        Returns:
            tuple[bool, str]: (can_update, reason)
        """
        now = datetime.now(timezone.utc)
        
        # Allow updates during calibration period
        if self.calibration_ends_at:
            calibration_end = datetime.fromisoformat(self.calibration_ends_at)
            if now < calibration_end:
                return True, "Calibration period active"

        # Check cooldown period (30 days)
        if self.last_rating_update:
            last_update = datetime.fromisoformat(self.last_rating_update)
            days_since_update = (now - last_update).days
            if days_since_update < 30:
                return False, f"Rating can be updated after {30 - days_since_update} days"

        return True, "Rating update allowed"
