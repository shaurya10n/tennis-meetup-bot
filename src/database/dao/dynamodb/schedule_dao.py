from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from src.database.models.dynamodb.schedule import Schedule


class ScheduleDAO:
    """Data Access Object for Schedule model in DynamoDB."""
    
    def __init__(self, dynamodb):
        """Initialize ScheduleDAO with DynamoDB resource."""
        self.table = dynamodb.Table(Schedule.TABLE_NAME)
    
    def create_schedule(self, guild_id: str, user_id: str, start_time: int, end_time: int, 
                       **kwargs) -> Schedule:
        """Create a new schedule in the database.
        
        Args:
            guild_id: Discord server ID
            user_id: Discord user ID
            start_time: Start time as Unix timestamp
            end_time: End time as Unix timestamp
            **kwargs: Additional schedule attributes
            
        Returns:
            Schedule: The created schedule object
        """
        import logging
        logger = logging.getLogger(__name__)
        
        import traceback
        logger.info(f"ScheduleDAO.create_schedule called - Guild: {guild_id}, User: {user_id}, Start: {start_time}, End: {end_time}")
        logger.info(f"Call stack: {''.join(traceback.format_stack()[-3:])}")
        
        schedule = Schedule(
            guild_id=guild_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            **kwargs
        )
        
        # Validate schedule before saving
        is_valid, error_message = schedule.is_valid()
        if not is_valid:
            raise ValueError(f"Invalid schedule: {error_message}")
        
        logger.info(f"Saving schedule to database - ID: {schedule.schedule_id}")
        self.table.put_item(Item=schedule.to_dict())
        logger.info(f"Schedule saved successfully - ID: {schedule.schedule_id}")
        
        return schedule
    
    def get_schedule(self, guild_id: str, schedule_id: str) -> Optional[Schedule]:
        """Get a schedule by Guild ID and schedule ID.
        
        Args:
            guild_id: Discord server ID
            schedule_id: Schedule ID
            
        Returns:
            Optional[Schedule]: The schedule object if found, None otherwise
        """
        response = self.table.get_item(
            Key={
                'guild_id': str(guild_id),
                'schedule_id': schedule_id
            }
        )
        item = response.get('Item')
        
        if not item:
            return None
            
        return Schedule.from_dict(item)
    
    def update_schedule(self, guild_id: str, schedule_id: str, 
                       **update_data) -> Schedule:
        """Update a schedule's attributes.
        
        Args:
            guild_id: Discord server ID
            schedule_id: Schedule ID
            **update_data: Attributes to update
            
        Returns:
            Schedule: The updated schedule object
        """
        # Get current schedule data
        schedule = self.get_schedule(guild_id, schedule_id)
        if not schedule:
            raise ValueError(f"Schedule with ID {schedule_id} not found for guild {guild_id}")
        
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
                'schedule_id': schedule_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values
        )
        
        # Return updated schedule
        return self.get_schedule(guild_id, schedule_id)
    
    def cancel_schedule(self, guild_id: str, schedule_id: str) -> bool:
        """Cancel a schedule by setting its status to 'cancelled'.
        
        Args:
            guild_id: Discord server ID
            schedule_id: Schedule ID
            
        Returns:
            bool: True if schedule was cancelled, False otherwise
        """
        try:
            self.update_schedule(guild_id, schedule_id, status="cancelled")
            return True
        except ValueError:
            return False
    
    def get_user_schedules(self, guild_id: str, user_id: str) -> List[Schedule]:
        """Get all schedules for a user in a guild.
        
        Args:
            guild_id: Discord server ID
            user_id: Discord user ID
            
        Returns:
            List[Schedule]: List of schedules for the user
        """
        response = self.table.query(
            IndexName="UserSchedulesIndex",
            KeyConditionExpression="user_id = :user_id",
            FilterExpression="guild_id = :guild_id",
            ExpressionAttributeValues={
                ":user_id": str(user_id),
                ":guild_id": str(guild_id)
            }
        )
        
        items = response.get('Items', [])
        schedules = [Schedule.from_dict(item) for item in items]
        return schedules
    
    def get_user_schedules_in_time_range(self, guild_id: str, user_id: str, 
                                       start_time: int, end_time: int) -> List[Schedule]:
        """Get all schedules for a user within a time range.
        
        Args:
            guild_id: Discord server ID
            user_id: Discord user ID
            start_time: Start time lower bound (Unix timestamp)
            end_time: End time upper bound (Unix timestamp)
            
        Returns:
            List[Schedule]: List of schedules for the user within the time range
        """
        response = self.table.query(
            IndexName="UserSchedulesIndex",
            KeyConditionExpression="user_id = :user_id AND start_time BETWEEN :start_time AND :end_time",
            FilterExpression="guild_id = :guild_id",
            ExpressionAttributeValues={
                ":user_id": str(user_id),
                ":guild_id": str(guild_id),
                ":start_time": start_time,
                ":end_time": end_time
            }
        )
        
        items = response.get('Items', [])
        schedules = [Schedule.from_dict(item) for item in items]
        return schedules
    
    def get_overlapping_schedules(self, guild_id: str, start_time: int, end_time: int, 
                                exclude_user_id: str = None) -> List[Schedule]:
        """Get all schedules that overlap with the given time range.
        
        Args:
            guild_id: Discord server ID
            start_time: Start time as Unix timestamp
            end_time: End time as Unix timestamp
            exclude_user_id: Optional Discord user ID to exclude from results
            
        Returns:
            List[Schedule]: List of overlapping schedules
        """
        # Build filter expression
        filter_expression = "guild_id = :guild_id AND start_time <= :end_time AND end_time >= :start_time"
        expression_values = {
            ":guild_id": str(guild_id),
            ":start_time": start_time,
            ":end_time": end_time
        }
        
        # Add user exclusion if specified
        if exclude_user_id:
            filter_expression += " AND user_id <> :exclude_user_id"
            expression_values[":exclude_user_id"] = str(exclude_user_id)
        
        # Add status filter to exclude cancelled schedules
        filter_expression += " AND #status <> :cancelled_status"
        expression_values[":cancelled_status"] = "cancelled"
        
        # Scan the table with filters
        response = self.table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames={"#status": "status"}
        )
        
        items = response.get('Items', [])
        schedules = [Schedule.from_dict(item) for item in items]
        return schedules
    
    def get_schedules_in_time_range(self, guild_id: str, start_time: int, end_time: int) -> List[Schedule]:
        """Get all schedules within a time range for a guild.
        
        Args:
            guild_id: Discord server ID
            start_time: Start time as Unix timestamp
            end_time: End time as Unix timestamp
            
        Returns:
            List[Schedule]: List of schedules within the time range
        """
        # Query using StartTimeIndex for each hour in the range
        schedules = []
        current_hour = start_time - (start_time % 3600)  # Round down to hour
        end_hour = end_time - (end_time % 3600) + 3600  # Round up to next hour
        
        while current_hour < end_hour:
            response = self.table.query(
                IndexName="StartTimeIndex",
                KeyConditionExpression="start_time = :hour",
                FilterExpression="guild_id = :guild_id",
                ExpressionAttributeValues={
                    ":hour": current_hour,
                    ":guild_id": str(guild_id)
                }
            )
            
            items = response.get('Items', [])
            schedules.extend([Schedule.from_dict(item) for item in items])
            current_hour += 3600  # Next hour
        
        return schedules
    
    def get_schedules_by_location(self, guild_id: str, location: str) -> List[Schedule]:
        """Get all schedules for a specific location in a guild.
        
        Args:
            guild_id: Discord server ID
            location: Location name
            
        Returns:
            List[Schedule]: List of schedules for the location
        """
        response = self.table.scan(
            FilterExpression="guild_id = :guild_id AND location = :location",
            ExpressionAttributeValues={
                ":guild_id": str(guild_id),
                ":location": location
            }
        )
        
        items = response.get('Items', [])
        schedules = [Schedule.from_dict(item) for item in items]
        return schedules
    
    def cancel_user_schedules(self, guild_id: str, user_id: str) -> int:
        """Cancel all schedules for a user by setting status to 'cancelled'.
        
        Args:
            guild_id: Discord server ID
            user_id: Discord user ID
            
        Returns:
            int: Number of schedules cancelled
        """
        schedules = self.get_user_schedules(guild_id, user_id)
        count = 0
        
        for schedule in schedules:
            if schedule.status != "cancelled":
                self.cancel_schedule(guild_id, schedule.schedule_id)
                count += 1
            
        return count
    
    def cancel_user_schedules_in_time_range(self, guild_id: str, user_id: str, 
                                         start_time: int, end_time: int) -> int:
        """Cancel all schedules for a user within a time range.
        
        Args:
            guild_id: Discord server ID
            user_id: Discord user ID
            start_time: Start time as Unix timestamp
            end_time: End time as Unix timestamp
            
        Returns:
            int: Number of schedules cancelled
        """
        schedules = self.get_user_schedules_in_time_range(guild_id, user_id, start_time, end_time)
        count = 0
        
        for schedule in schedules:
            if schedule.status != "cancelled":
                self.cancel_schedule(guild_id, schedule.schedule_id)
                count += 1
            
        return count
