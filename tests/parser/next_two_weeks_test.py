"""Test for the 'next two weeks' pattern."""

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
    """Test the 'next two weeks' pattern specifically."""
    parser = TimeParser()
    
    # Test cases
    test_cases = [
        "next two weeks 3-5pm",
        "next two weeks 3pm to 5pm",
        "next 2 weeks 3-5pm",
        "next 2 weeks 3pm to 5pm"
    ]
    
    print("\n===== NEXT TWO WEEKS PATTERN TEST =====\n")
    
    for i, time_desc in enumerate(test_cases):
        print(f"Test {i+1}: '{time_desc}'")
        start_time, end_time, error = parser.parse_time_description(time_desc)
        
        if error:
            print(f"❌ Error: {error}")
        else:
            print(f"✅ Successfully parsed")
            print(f"   Start: {start_time}")
            print(f"   End: {end_time}")
            
            # Check if the date is actually two weeks from now
            today = datetime.now(ZoneInfo("America/Vancouver")).replace(hour=0, minute=0, second=0, microsecond=0)
            expected_date = today + timedelta(days=14)
            if start_time.date() == expected_date.date():
                print(f"   ✅ Correct date: {start_time.date()} is two weeks from today")
            else:
                print(f"   ❌ Incorrect date: {start_time.date()} is not two weeks from today ({expected_date.date()})")
        
        print("")

if __name__ == "__main__":
    main()
