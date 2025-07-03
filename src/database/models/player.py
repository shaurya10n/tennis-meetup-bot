# src/database/models/player.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Player:
    """Player model representing a tennis player in the system.

    Attributes:
        user_id (int): Discord user ID
        username (str): Discord username
        ntrp_rating (float): NTRP rating (2.0-5.0)
        interests (List[str]): List of tennis interests
        knows_ntrp (bool): Whether user knew their NTRP rating
        rating_responses (Optional[Dict]): Stored responses if rating was calculated
        calibration_ends_at (Optional[datetime]): When 2-week calibration period ends
        last_rating_update (Optional[datetime]): Last time rating was updated
        created_at (Optional[datetime]): When profile was created
        updated_at (Optional[datetime]): Last update timestamp
        skill_level_preferences (List[str]): Preferred opponent skill levels
        gender_preference (str): Gender preference for matches (none/men/women)
    """
    user_id: int
    username: str
    ntrp_rating: float
    interests: List[str]
    knows_ntrp: bool
    preferred_locations: List[str] = field(default_factory=list)
    rating_responses: Optional[Dict] = None
    calibration_ends_at: Optional[datetime] = None
    last_rating_update: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    skill_level_preferences: List[str] = field(default_factory=list)  # Changed to list
    gender_preference: str = "none"  # Default to no preference

    def to_dict(self) -> dict:
        """Convert player to dictionary for database storage."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "ntrp_rating": self.ntrp_rating,
            "interests": self.interests,
            "knows_ntrp": self.knows_ntrp,
            "rating_responses": self.rating_responses,
            "calibration_ends_at": self.calibration_ends_at,
            "last_rating_update": self.last_rating_update,
            "preferred_locations": self.preferred_locations,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "skill_level_preferences": self.skill_level_preferences,  # Updated field name
            "gender_preference": self.gender_preference
        }

    @staticmethod
    def from_dict(data: dict) -> 'Player':
        """Create player instance from dictionary."""
        return Player(
            user_id=data.get('user_id'),
            username=data.get('username'),
            ntrp_rating=data.get('ntrp_rating'),
            interests=data.get('interests', []),
            knows_ntrp=data.get('knows_ntrp', False),
            rating_responses=data.get('rating_responses'),
            calibration_ends_at=data.get('calibration_ends_at'),
            last_rating_update=data.get('last_rating_update'),
            preferred_locations=data.get('preferred_locations', []),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            skill_level_preferences=data.get('skill_level_preferences', []),  # Updated field name
            gender_preference=data.get('gender_preference', 'none')
        )

    def is_profile_complete(self) -> tuple[bool, list[str]]:
        """Check if player profile is complete.

        Returns:
            tuple[bool, list[str]]: (is_complete, missing_fields)
            where missing_fields is a list of field names that need to be completed
        """
        missing_fields = []
        
        if self.ntrp_rating is None:
            missing_fields.append("NTRP rating")
        if not self.interests:
            missing_fields.append("tennis interests")
        if not self.preferred_locations:
            missing_fields.append("preferred locations")
        if not self.skill_level_preferences:
            missing_fields.append("skill level preferences")
        # "none" is a valid preference meaning "No Preference"
        if not self.gender_preference:
            missing_fields.append("gender preference")
            
        return (len(missing_fields) == 0, missing_fields)

    def can_update_rating(self) -> tuple[bool, str]:
        """Check if player can update their NTRP rating.

        Returns:
            tuple[bool, str]: (can_update, reason)
        """
        now = datetime.now()

        # Allow updates during calibration period
        if self.calibration_ends_at and now < self.calibration_ends_at:
            return True, "Calibration period active"

        # Check cooldown period (30 days)
        if self.last_rating_update:
            days_since_update = (now - self.last_rating_update).days
            if days_since_update < 30:
                return False, f"Rating can be updated after {30 - days_since_update} days"

        return True, "Rating update allowed"
