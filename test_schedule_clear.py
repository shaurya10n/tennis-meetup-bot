#!/usr/bin/env python3
"""Test script to verify schedule clearing functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.dynamodb_config import get_db
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def test_schedule_clear():
    """Test the schedule clearing functionality."""
    try:
        # Initialize DAO
        db = get_db()
        schedule_dao = ScheduleDAO(db)
        
        # Test guild and user IDs
        guild_id = "1234567890123456789"
        user_id = "123456789"
        
        print(f"Testing schedule clearing for user {user_id} in guild {guild_id}")
        
        # Get current time
        now = datetime.now(ZoneInfo("America/Vancouver"))
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        start_timestamp = int(today_start.timestamp())
        end_timestamp = int(today_end.timestamp())
        
        print(f"Testing time range: {today_start} - {today_end}")
        print(f"Timestamps: {start_timestamp} - {end_timestamp}")
        
        # First, get schedules in the time range
        print("\nGetting schedules in time range...")
        schedules = schedule_dao.get_user_schedules_in_time_range(
            guild_id, user_id, start_timestamp, end_timestamp
        )
        
        print(f"Found {len(schedules)} schedules in time range:")
        for schedule in schedules:
            start_time = datetime.fromtimestamp(schedule.start_time)
            end_time = datetime.fromtimestamp(schedule.end_time)
            print(f"  - {start_time} - {end_time} (Status: {schedule.status})")
        
        # Test clearing schedules
        print("\nTesting schedule clearing...")
        count = schedule_dao.cancel_user_schedules_in_time_range(
            guild_id, user_id, start_timestamp, end_timestamp
        )
        
        print(f"Cleared {count} schedules")
        
        # Check schedules again
        print("\nChecking schedules after clearing...")
        schedules_after = schedule_dao.get_user_schedules_in_time_range(
            guild_id, user_id, start_timestamp, end_timestamp
        )
        
        print(f"Found {len(schedules_after)} schedules after clearing:")
        for schedule in schedules_after:
            start_time = datetime.fromtimestamp(schedule.start_time)
            end_time = datetime.fromtimestamp(schedule.end_time)
            print(f"  - {start_time} - {end_time} (Status: {schedule.status})")
        
        print("\n✅ Schedule clearing test completed successfully!")
        
    except Exception as e:
        print(f"Error testing schedule clearing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_schedule_clear() 