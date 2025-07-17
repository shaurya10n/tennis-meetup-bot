"""Schedule data aggregator for the availability dashboard."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from zoneinfo import ZoneInfo

from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.database.models.schedule import Schedule
from src.database.models.player import Player
from src.utils.config_loader import ConfigLoader
from .constants import TIME_SLOTS

logger = logging.getLogger(__name__)

class ScheduleAggregator:
    """Aggregates schedule data for the availability dashboard."""

    def __init__(self, schedule_dao: ScheduleDAO, player_dao: PlayerDAO, court_dao: CourtDAO):
        """Initialize with DAOs.
        
        Args:
            schedule_dao (ScheduleDAO): Schedule data access object
            player_dao (PlayerDAO): Player data access object
            court_dao (CourtDAO): Court data access object
        """
        self.schedule_dao = schedule_dao
        self.player_dao = player_dao
        self.court_dao = court_dao
        config_loader = ConfigLoader()
        self.timezone = config_loader.get_timezone()

    async def get_locations(self) -> List[str]:
        """Get all unique locations from the courts database.
        
        Returns:
            List[str]: List of unique locations
        """
        # Get all courts and extract unique locations
        courts = self.court_dao.list_courts()
        locations = list(set(court.location for court in courts))
        
        # If no locations found, return a default list to avoid empty dashboard
        if not locations:
            logger.warning("No court locations found in database, using default locations")
            return ["Downtown Courts", "West Side Club", "Eastside Tennis Center"]
            
        return locations

    async def get_availability_by_location(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        location: Optional[str] = None
    ) -> Dict[str, Dict[str, Dict[str, List[int]]]]:
        """Get availability data grouped by location.
        
        Args:
            start_date (datetime, optional): Start date for availability data
            end_date (datetime, optional): End date for availability data
            location (str, optional): Filter by specific location
            
        Returns:
            Dict: Nested dictionary with structure:
                {
                    "Location Name": {
                        "YYYY-MM-DD": {
                            "Morning": [user_id1, user_id2, ...],
                            "Afternoon": [user_id3, ...],
                            "Evening": [user_id4, ...]
                        }
                    }
                }
        """
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.now(self.timezone).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        if not end_date:
            end_date = start_date + timedelta(days=7)
            
        # Get all schedules within the date range
        # Convert datetime to timestamp for DynamoDB
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        
        # Use get_schedules_in_time_range since get_all_schedules doesn't exist in DynamoDB version
        schedules = self.schedule_dao.get_schedules_in_time_range(
            start_timestamp,
            end_timestamp
        )
        
        # Get all locations if not filtering by a specific one
        locations = [location] if location else await self.get_locations()
        
        # Initialize result structure
        result = {loc: {} for loc in locations}
        
        # Process each schedule
        for schedule in schedules:
            # Get schedule location
            schedule_location = await self._get_schedule_location(schedule)
            
            # Skip if location doesn't match filter
            if location and schedule_location != location:
                continue
                
            # Skip if location not in our list
            if schedule_location not in locations:
                continue
                
            # Process schedule dates
            current_date = max(schedule.start_time, start_date)
            end_date_schedule = min(schedule.end_time, end_date)
            
            while current_date < end_date_schedule:
                date_str = current_date.strftime("%Y-%m-%d")
                
                # Initialize date in result if needed
                if date_str not in result[schedule_location]:
                    result[schedule_location][date_str] = {
                        "Morning": [],
                        "Afternoon": [],
                        "Evening": []
                    }
                
                # Determine time slot
                time_slot = self._get_time_slot(current_date)
                
                # Add user to time slot if not already there
                if time_slot and schedule.user_id not in result[schedule_location][date_str][time_slot]:
                    result[schedule_location][date_str][time_slot].append(schedule.user_id)
                
                # Move to next hour
                current_date += timedelta(hours=1)
        
        return result

    async def get_currently_playing(self) -> Dict[str, List[Tuple[int, datetime, datetime]]]:
        """Get users currently playing grouped by location.
        
        Returns:
            Dict[str, List[Tuple[int, datetime, datetime]]]: 
                Dictionary mapping locations to lists of (user_id, start_time, end_time) tuples
        """
        now = datetime.now(self.timezone)
        
        # Get schedules that include the current time
        # Convert datetime to timestamp for DynamoDB
        start_timestamp = int((now - timedelta(hours=3)).timestamp())
        end_timestamp = int((now + timedelta(hours=1)).timestamp())
        
        # Use get_schedules_in_time_range since get_all_schedules doesn't exist in DynamoDB version
        schedules = self.schedule_dao.get_schedules_in_time_range(
            start_timestamp,
            end_timestamp
        )
        
        # Filter to only include schedules that are currently active
        active_schedules = [s for s in schedules if s.start_time <= now <= s.end_time]
        
        # Group by location
        result = {}
        for schedule in active_schedules:
            location = await self._get_schedule_location(schedule)
            
            if location not in result:
                result[location] = []
                
            result[location].append((schedule.user_id, schedule.start_time, schedule.end_time))
            
        return result

    async def get_user_dict(self, user_ids: Set[int]) -> Dict[int, Dict]:
        """Get user information for a set of user IDs.
        
        Args:
            user_ids (Set[int]): Set of user IDs
            
        Returns:
            Dict[int, Dict]: Dictionary mapping user IDs to user info dictionaries
        """
        result = {}
        
        for user_id in user_ids:
            player = self.player_dao.get_player(str(user_id))
            if player:
                result[user_id] = {
                    "username": player.username,
                    "ntrp_rating": player.ntrp_rating
                }
                
        return result

    async def _get_schedule_location(self, schedule: Schedule) -> str:
        """Get the location for a schedule.
        
        Args:
            schedule (Schedule): Schedule to get location for
            
        Returns:
            str: Location name
        """
        # First check if schedule has a specific location set
        if not schedule.use_profile_preferences and schedule.location:
            return schedule.location
            
        # Then check player's preferred locations
        player = self.player_dao.get_player(str(schedule.user_id))
        if player and player.preferred_locations:
            return player.preferred_locations[0]
            
        # If no location found, get the first available court location
        locations = await self.get_locations()
        if locations:
            return locations[0]
            
        # Absolute fallback if no locations exist
        return "Unknown Location"

    def _get_time_slot(self, dt: datetime) -> Optional[str]:
        """Get the time slot for a datetime.
        
        Args:
            dt (datetime): Datetime to get time slot for
            
        Returns:
            Optional[str]: Time slot name or None if outside all time slots
        """
        hour = dt.hour
        
        for slot_name, (start_hour, end_hour) in TIME_SLOTS.items():
            if start_hour <= hour < end_hour:
                return slot_name
                
        return None
