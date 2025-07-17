"""Schedule model for DynamoDB."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from zoneinfo import ZoneInfo
from decimal import Decimal
from src.utils.config_loader import ConfigLoader


class Schedule:
    """Schedule model for DynamoDB representing a player's availability."""
    
    TABLE_NAME = "Schedules"
    
    @staticmethod
    def create_table(dynamodb):
        """Create the Schedules table in DynamoDB if it doesn't exist."""
        table = dynamodb.create_table(
            TableName=Schedule.TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'guild_id', 'KeyType': 'HASH'},     # Partition key
                {'AttributeName': 'schedule_id', 'KeyType': 'RANGE'}   # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'guild_id', 'AttributeType': 'S'},
                {'AttributeName': 'schedule_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'start_time', 'AttributeType': 'N'},
                {'AttributeName': 'parent_schedule_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserSchedulesIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'start_time', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                },
                {
                    'IndexName': 'StartTimeIndex',
                    'KeySchema': [
                        {'AttributeName': 'start_time', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                },
                {
                    'IndexName': 'RecurringInstancesIndex',
                    'KeySchema': [
                        {'AttributeName': 'parent_schedule_id', 'KeyType': 'HASH'},
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
                 user_id: str,
                 start_time: int,  # Unix timestamp
                 end_time: int,    # Unix timestamp
                 schedule_id: str = None,
                 parent_schedule_id: str = None,
                 recurrence: Optional[Dict[str, Any]] = None,
                 preference_overrides: Optional[Dict[str, Any]] = None,
                 status: str = "open",
                 match_id: Optional[str] = None,
                 created_at: Optional[str] = None,  # ISO format with UTC timezone
                 updated_at: Optional[str] = None,  # ISO format with UTC timezone
                 timezone_str: str = None):
        """Initialize a Schedule instance."""
        self.guild_id = str(guild_id)
        self.user_id = str(user_id)
        self.schedule_id = schedule_id or str(uuid.uuid4())
        self.start_time = start_time
        self.end_time = end_time
        self.parent_schedule_id = parent_schedule_id
        self.recurrence = recurrence
        self.preference_overrides = preference_overrides or {}
        self.status = status
        self.match_id = match_id
        
        # Set timestamps with ISO format
        now_iso = datetime.now(timezone.utc).isoformat()
        self.created_at = created_at or now_iso
        self.updated_at = updated_at or now_iso
        
        # Use configured timezone if not provided
        if timezone_str is None:
            config_loader = ConfigLoader()
            self.timezone_str = str(config_loader.get_timezone())
        else:
            self.timezone_str = timezone_str
        self.timezone = ZoneInfo(self.timezone_str)
    
    def to_dict(self) -> dict:
        """Convert schedule to dictionary for DynamoDB storage."""
        data = {
            "guild_id": self.guild_id,
            "user_id": self.user_id,
            "schedule_id": self.schedule_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "preference_overrides": self.preference_overrides,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "timezone": self.timezone_str
        }
        
        # Only include these fields if they have values
        if self.parent_schedule_id:
            data["parent_schedule_id"] = self.parent_schedule_id
        if self.recurrence:
            data["recurrence"] = self.recurrence
        if self.match_id:
            data["match_id"] = self.match_id
            
        return data
    
    @staticmethod
    def from_dict(data: dict) -> 'Schedule':
        """Create schedule instance from dictionary."""
        # Convert timestamp fields to int if they exist
        start_time = data.get('start_time')
        if start_time is not None:
            start_time = int(start_time)
            
        end_time = data.get('end_time')
        if end_time is not None:
            end_time = int(end_time)
        
        # Handle recurrence 'until' field if it exists
        recurrence = data.get('recurrence')
        if recurrence and 'until' in recurrence and recurrence['until'] is not None:
            recurrence['until'] = int(recurrence['until'])
        
        return Schedule(
            guild_id=data.get('guild_id'),
            user_id=data.get('user_id'),
            schedule_id=data.get('schedule_id'),
            start_time=start_time,
            end_time=end_time,
            parent_schedule_id=data.get('parent_schedule_id'),
            recurrence=recurrence,
            preference_overrides=data.get('preference_overrides', {}),
            status=data.get('status', 'open'),
            match_id=data.get('match_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            timezone_str=data.get('timezone')  # Will use configured timezone if None
        )
    
    def to_datetime(self, timestamp: int) -> datetime:
        """Convert timestamp to timezone-aware datetime."""
        dt = datetime.fromtimestamp(timestamp)
        return dt.replace(tzinfo=self.timezone)
    
    def from_datetime(self, dt: datetime) -> int:
        """Convert datetime to timestamp."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.timezone)
        return int(dt.timestamp())
    
    def overlaps_with(self, other: 'Schedule') -> bool:
        """Check if this schedule overlaps with another schedule."""
        return (
            (self.start_time <= other.start_time < self.end_time) or
            (other.start_time <= self.start_time < other.end_time)
        )
    
    def duration_minutes(self) -> int:
        """Get the duration of the schedule in minutes."""
        return int((self.end_time - self.start_time) / 60)
    
    def is_valid(self) -> Tuple[bool, str]:
        """Validate the schedule.
        
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        if self.start_time >= self.end_time:
            return False, "End time must be after start time"
        
        if self.duration_minutes() > 240:  # 4 hours max
            return False, "Schedule duration cannot exceed 4 hours"
        
        if self.start_time < int(datetime.now().timestamp()):
            return False, "Cannot create schedule in the past"
        
        if self.recurrence:
            if not isinstance(self.recurrence, dict):
                return False, "Invalid recurrence format"
            
            if 'type' not in self.recurrence:
                return False, "Recurrence must specify type"
            
            if self.recurrence['type'] not in ['daily', 'weekly', 'monthly']:
                return False, "Invalid recurrence type"
            
            if 'until' in self.recurrence and not isinstance(self.recurrence['until'], int):
                return False, "Invalid recurrence end date"
        
        return True, ""
    
    def is_recurring_parent(self) -> bool:
        """Check if this schedule is a parent recurring schedule."""
        return self.parent_schedule_id is None and self.recurrence is not None
    
    def is_recurring_instance(self) -> bool:
        """Check if this schedule is an instance of a recurring schedule."""
        return self.parent_schedule_id is not None
    
    def is_standalone(self) -> bool:
        """Check if this schedule is a standalone (non-recurring) schedule."""
        return self.parent_schedule_id is None and self.recurrence is None
    
    def get_next_occurrence(self, after_timestamp: int) -> Optional[int]:
        """Get the next occurrence of this schedule after the given time.
        
        Args:
            after_timestamp (int): Time to find next occurrence after (Unix timestamp)

        Returns:
            Optional[int]: Next occurrence time or None if no more occurrences
        """
        # Convert timestamps to datetime for easier manipulation
        after_dt = datetime.fromtimestamp(after_timestamp, tz=self.timezone)
        start_dt = datetime.fromtimestamp(self.start_time, tz=self.timezone)
        
        # For non-recurring schedules, just check if it's in the future
        if not self.recurrence:
            if self.start_time > after_timestamp:
                return self.start_time
            return None
        
        # Get recurrence type and end date
        recurrence_type = self.recurrence.get('type')
        until_timestamp = self.recurrence.get('until')
        
        # If we're past the end date, no more occurrences
        if until_timestamp and after_timestamp > until_timestamp:
            return None
        
        # Calculate next occurrence based on recurrence type
        if recurrence_type == 'daily':
            # Calculate days since the start date
            days_since_start = (after_dt.date() - start_dt.date()).days
            if days_since_start < 0:
                # The start date is in the future
                return self.start_time
            
            # Calculate the next occurrence
            next_date = start_dt + timedelta(days=days_since_start + 1)
            return int(next_date.timestamp())
        
        elif recurrence_type == 'weekly':
            # Get the days of the week this schedule occurs on
            days = self.recurrence.get('days', [])
            
            # If no specific days are specified, use the day of the week from start_time
            if not days:
                days = [start_dt.strftime('%A').lower()]
            
            # Convert day names to day numbers (0=Monday, 6=Sunday)
            day_to_num = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            day_nums = [day_to_num.get(day.lower()) for day in days if day.lower() in day_to_num]
            
            # If the start date is in the future, return it
            if self.start_time > after_timestamp:
                return self.start_time
            
            # Find the next occurrence
            current_date = after_dt.date()
            for _ in range(7):  # Check the next 7 days
                current_date = current_date + timedelta(days=1)
                if current_date.weekday() in day_nums:
                    # Found the next day that matches
                    next_date = datetime.combine(
                        current_date,
                        start_dt.time(),
                        tzinfo=self.timezone
                    )
                    return int(next_date.timestamp())
        
        elif recurrence_type == 'monthly':
            # If the start date is in the future, return it
            if self.start_time > after_timestamp:
                return self.start_time
            
            # Get the day of the month from the start date
            target_day = start_dt.day
            
            # Calculate the next occurrence
            next_date = after_dt.replace(day=1)  # First day of current month
            
            # Move to next month if we're past the target day in current month
            if after_dt.day >= target_day:
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
                start_dt.time(),
                tzinfo=self.timezone
            )
            
            return int(next_date.timestamp())
        
        # Default case if recurrence type is not recognized
        return None
