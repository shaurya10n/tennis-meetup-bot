"""Test for the 'rest of the week' pattern."""

import sys
import os
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import just the TimeParser class
from src.cogs.user.commands.schedule.parser.nlp_parser import TimeParser

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    """Test the 'rest of the week' pattern specifically."""
    parser = TimeParser()
    
    # Test cases with future times to avoid "in the past" errors
    test_cases = [
        "rest of the week 11-11:30pm",  # Late night time to avoid "in the past" errors
        "rest of the week 11pm to 11:30pm",
        "this week 11-11:30pm",
    ]
    
    print("\n===== REST OF WEEK PATTERN TEST =====\n")
    
    for i, time_desc in enumerate(test_cases):
        print(f"Test {i+1}: '{time_desc}'")
        start_time, end_time, error = parser.parse_time_description(time_desc)
        
        if error:
            print(f"❌ Error: {error}")
        else:
            print(f"✅ Successfully parsed")
            print(f"   Start: {start_time}")
            print(f"   End: {end_time}")
            
            # Check if the date is today
            today = datetime.now(ZoneInfo("America/Vancouver")).replace(hour=0, minute=0, second=0, microsecond=0)
            if start_time.date() == today.date():
                print(f"   ✅ Correct date: {start_time.date()} is today")
            else:
                print(f"   ❌ Incorrect date: {start_time.date()} is not today ({today.date()})")
        
        print("")

if __name__ == "__main__":
    main()
