"""Simple test for the enhanced time parser."""

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
    """Test the TimeParser with various inputs."""
    parser = TimeParser()
    
    # Test cases
    test_cases = [
        "today 4-6pm",
        "tomorrow 3-5pm",
        "next monday 2-4pm",
        "next week tuesday 3-5pm",
        "every monday 4-6pm",
        "next two weeks 3pm to 5pm",
        "rest of the week 4-5 pm",
        "tomorrow afternoon",
        "next friday evening"
    ]
    
    print("\n===== TIME PARSER TEST RESULTS =====\n")
    
    for i, time_desc in enumerate(test_cases):
        print(f"Test {i+1}: '{time_desc}'")
        start_time, end_time, error = parser.parse_time_description(time_desc)
        
        if error:
            print(f"❌ Error: {error}")
        else:
            print(f"✅ Successfully parsed")
            print(f"   Start: {start_time}")
            print(f"   End: {end_time}")
            
            # Check for recurrence
            recurrence = parser._extract_recurrence_pattern(time_desc)
            if recurrence:
                print(f"   Recurrence: {recurrence}")
        
        print("")

if __name__ == "__main__":
    main()
