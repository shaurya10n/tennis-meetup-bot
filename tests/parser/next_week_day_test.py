"""Test specific cases for next week day parsing."""

import sys
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.cogs.user.commands.schedule.parser.nlp_parser import TimeParser

def test_next_week_day_parsing():
    """Test parsing of 'next week day' patterns."""
    parser = TimeParser()
    
    # Get current time in Vancouver timezone
    tz = ZoneInfo("America/Vancouver")
    now = datetime.now(tz)
    
    # Test cases for each day of the week
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    print("\n===== NEXT WEEK DAY PARSING TEST =====\n")
    
    for day in days:
        time_desc = f"next week {day} 4-5pm"
        print(f"Testing: '{time_desc}'")
        
        start_time, end_time, error = parser.parse_time_description(time_desc)
        
        if error:
            print(f"❌ FAILED: Got error: {error}")
            continue
            
        # Calculate expected date
        # First get to next Monday
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
        
        # Then add days needed to reach target day
        day_num = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }[day]
        expected_date = next_monday + timedelta(days=day_num)
        
        # Set expected times
        expected_start = expected_date.replace(hour=16, minute=0)  # 4 PM
        expected_end = expected_date.replace(hour=17, minute=0)    # 5 PM
        
        # Compare results
        if start_time.date() == expected_start.date():
            print(f"✅ PASSED: Date matches expected ({start_time.date()})")
            if start_time.hour == expected_start.hour and end_time.hour == expected_end.hour:
                print(f"✅ PASSED: Time range matches expected (4-5pm)")
            else:
                print(f"❌ FAILED: Time range mismatch. Expected 4-5pm, got {start_time.hour}-{end_time.hour}")
        else:
            print(f"❌ FAILED: Date mismatch")
            print(f"   Expected: {expected_start.date()}")
            print(f"   Got: {start_time.date()}")
        
        print("")

if __name__ == "__main__":
    test_next_week_day_parsing()
