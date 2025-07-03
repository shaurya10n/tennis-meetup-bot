# src/database/models/schedule.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from zoneinfo import ZoneInfo
from google.cloud import firestore

@dataclass
class Schedule:
    """Schedule model representing a player's availability.

    Attributes:
        user_id (int): Discord user ID
        start_time (datetime): Start time of availability
        end_time (datetime): End time of availability
        recurrence (Optional[Dict[str, Any]]): Recurrence pattern if any
            Example: {
                'type': 'weekly',
                'days': ['monday', 'wednesday'],
                'until': datetime(2024, 12, 31)
            }
        location (Optional[str]): Preferred location for this schedule
        skill_level_preference (Optional[List[str]]): Preferred skill levels for this schedule
        gender_preference (Optional[str]): Gender preference for this schedule
        use_profile_preferences (bool): Whether to use preferences from player's profile
        created_at (datetime): When schedule was created
        updated_at (Optional[datetime]): Last update timestamp
    """
    user_id: int
    start_time: datetime
    end_time: datetime
    recurrence: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    skill_level_preference: Optional[List[str]] = None
    gender_preference: Optional[str] = "none"
    use_profile_preferences: bool = True  # Default to using profile preferences
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    timezone: ZoneInfo = ZoneInfo("America/Vancouver")  # TODO: Make configurable

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(self.timezone)

        # Ensure all datetimes are timezone-aware
        if self.start_time.tzinfo is None:
            self.start_time = self.start_time.replace(tzinfo=self.timezone)
        if self.end_time.tzinfo is None:
            self.end_time = self.end_time.replace(tzinfo=self.timezone)
        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=self.timezone)
        if self.updated_at and self.updated_at.tzinfo is None:
            self.updated_at = self.updated_at.replace(tzinfo=self.timezone)

        # Clean seconds and microseconds
        self.start_time = self.start_time.replace(second=0, microsecond=0)
        self.end_time = self.end_time.replace(second=0, microsecond=0)
        self.created_at = self.created_at.replace(second=0, microsecond=0)
        if self.updated_at:
            self.updated_at = self.updated_at.replace(second=0, microsecond=0)

    def to_dict(self) -> dict:
        """Convert schedule to dictionary for database storage."""
        return {
            "user_id": self.user_id,
            "start_time": self.start_time,  # Store as Firestore timestamp
            "end_time": self.end_time,      # Store as Firestore timestamp
            "recurrence": self.recurrence,
            "location": self.location,
            "skill_level_preference": self.skill_level_preference,
            "gender_preference": self.gender_preference,
            "created_at": self.created_at,   # Store as Firestore timestamp
            "updated_at": self.updated_at,    # Store as Firestore timestamp
            "use_profile_preferences": self.use_profile_preferences
        }

    @staticmethod
    def from_dict(data: dict) -> 'Schedule':
        """Create schedule instance from dictionary."""
        timezone = ZoneInfo("America/Vancouver")  # TODO: Make configurable

        # Convert Firestore timestamps to datetime
        def to_datetime(value) -> Optional[datetime]:
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=timezone)
                return value.replace(second=0, microsecond=0)  # Clean seconds/microseconds
            return None

        return Schedule(
            user_id=data.get('user_id'),
            start_time=to_datetime(data.get('start_time')),
            end_time=to_datetime(data.get('end_time')),
            recurrence=data.get('recurrence'),
            location=data.get('location'),
            skill_level_preference=data.get('skill_level_preference'),
            gender_preference=data.get('gender_preference', 'none'),
            created_at=to_datetime(data.get('created_at')),
            updated_at=to_datetime(data.get('updated_at')),
            use_profile_preferences=data.get('use_profile_preferences', True)  # Default to True
        )

    def overlaps_with(self, other: 'Schedule') -> bool:
        """Check if this schedule overlaps with another schedule."""
        return (
            (self.start_time <= other.start_time < self.end_time) or
            (other.start_time <= self.start_time < other.end_time)
        )

    def duration_minutes(self) -> int:
        """Get the duration of the schedule in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def is_valid(self) -> tuple[bool, str]:
        """Validate the schedule.
        
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        if self.start_time >= self.end_time:
            return False, "End time must be after start time"
        
        if self.duration_minutes() > 240:  # 4 hours max
            return False, "Schedule duration cannot exceed 4 hours"

        if self.start_time < datetime.now(self.timezone).replace(second=0, microsecond=0):
            return False, "Cannot create schedule in the past"

        if self.recurrence:
            if not isinstance(self.recurrence, dict):
                return False, "Invalid recurrence format"
            
            if 'type' not in self.recurrence:
                return False, "Recurrence must specify type"
            
            if self.recurrence['type'] not in ['daily', 'weekly', 'monthly']:
                return False, "Invalid recurrence type"
            
            if 'until' in self.recurrence and not isinstance(self.recurrence['until'], datetime):
                return False, "Invalid recurrence end date"

        return True, ""

    def get_next_occurrence(self, after: datetime) -> Optional[datetime]:
        """Get the next occurrence of this schedule after the given time.
        
        Args:
            after (datetime): Time to find next occurrence after

        Returns:
            Optional[datetime]: Next occurrence time or None if no more occurrences
        """
        # Ensure after is timezone-aware and clean
        if after.tzinfo is None:
            after = after.replace(tzinfo=self.timezone)
        after = after.replace(second=0, microsecond=0)

        # For non-recurring schedules, just check if it's in the future
        if not self.recurrence:
            if self.start_time > after:
                return self.start_time
            return None

        # Get recurrence type and end date
        recurrence_type = self.recurrence.get('type')
        until_date = self.recurrence.get('until')
        
        # If we're past the end date, no more occurrences
        if until_date and after > until_date:
            return None
            
        # Calculate next occurrence based on recurrence type
        if recurrence_type == 'daily':
            # Calculate days since the start date
            days_since_start = (after.date() - self.start_time.date()).days
            if days_since_start < 0:
                # The start date is in the future
                return self.start_time
                
            # Calculate the next occurrence
            next_date = self.start_time + timedelta(days=days_since_start + 1)
            return next_date
            
        elif recurrence_type == 'weekly':
            # Get the days of the week this schedule occurs on
            days = self.recurrence.get('days', [])
            
            # If no specific days are specified, use the day of the week from start_time
            if not days:
                days = [self.start_time.strftime('%A').lower()]
                
            # Convert day names to day numbers (0=Monday, 6=Sunday)
            day_to_num = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            day_nums = [day_to_num.get(day.lower()) for day in days if day.lower() in day_to_num]
            
            # If the start date is in the future, return it
            if self.start_time > after:
                return self.start_time
                
            # Find the next occurrence
            current_date = after.date()
            for _ in range(7):  # Check the next 7 days
                current_date = current_date + timedelta(days=1)
                if current_date.weekday() in day_nums:
                    # Found the next day that matches
                    next_date = datetime.combine(
                        current_date,
                        self.start_time.time(),
                        tzinfo=self.timezone
                    )
                    return next_date
                    
        elif recurrence_type == 'monthly':
            # If the start date is in the future, return it
            if self.start_time > after:
                return self.start_time
                
            # Get the day of the month from the start date
            target_day = self.start_time.day
            
            # Calculate the next occurrence
            next_date = after.replace(day=1)  # First day of current month
            
            # Move to next month if we're past the target day in current month
            if after.day >= target_day:
                if next_date.month == 12:
                    next_date = next_date.replace(year=next_date.year + 1, month=1)
                else:
                    next_date = next_date.replace(month=next_date.month + 1)
                    
            # Set the target day, handling month length issues
            month_length = [31, 29 if next_date.year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            actual_day = min(target_day, month_length[next_date.month - 1])
            next_date = next_date.replace(day=actual_day)
            
            # Set the time from the original schedule
            next_date = datetime.combine(
                next_date.date(),
                self.start_time.time(),
                tzinfo=self.timezone
            )
            
            return next_date
            
        # Default case if recurrence type is not recognized
        return None
