"""Test the enhanced time parser."""

import sys
import os
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cogs.user.commands.schedule.parser.nlp_parser import TimeParser

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_time_parser():
    """Test the enhanced time parser with various inputs."""
    parser = TimeParser()
    
    # Test cases with expected results
    test_cases = [
        # Basic time formats
        ("today 4-6pm", True),
        ("tomorrow 3-5pm", True),
        ("next monday 2-4pm", True),
        
        # Complex formats from examples
        ("next week tuesday 3-5pm", True),
        ("every monday 4-6pm", True),
        ("next two weeks 3pm to 5pm", True),
        ("rest of the week 4-5 pm", True),
        
        # Time of day references
        ("tomorrow afternoon", True),
        ("next friday evening", True),
        
        # Typos and variations
        ("tomorow 3-5pm", True),  # Missing 'r'
        ("nxt monday 2-4pm", True),  # Missing 'e'
        ("evry day 9-10am", True),  # Missing 'e'
        
        # Invalid formats (should fail gracefully)
        ("invalid time", False),
        ("", False),
    ]
    
    print("\n===== TIME PARSER TEST RESULTS =====\n")
    
    for i, (time_desc, should_succeed) in enumerate(test_cases):
        print(f"Test {i+1}: '{time_desc}'")
        start_time, end_time, error = parser.parse_time_description(time_desc)
        
        if should_succeed:
            if error:
                print(f"❌ FAILED: Expected success but got error: {error}")
            else:
                print(f"✅ PASSED: Successfully parsed")
                print(f"   Start: {start_time}")
                print(f"   End: {end_time}")
                
                # Check for recurrence
                recurrence = parser._extract_recurrence_pattern(time_desc)
                if recurrence:
                    print(f"   Recurrence: {recurrence}")
        else:
            if error:
                print(f"✅ PASSED: Expected failure and got error: {error}")
            else:
                print(f"❌ FAILED: Expected failure but parsing succeeded")
                print(f"   Start: {start_time}")
                print(f"   End: {end_time}")
        
        print("")
    
    print("===== ADDITIONAL FUZZY MATCHING TESTS =====\n")
    
    # Test fuzzy matching
    fuzzy_tests = [
        "tomorow",
        "nxt week",
        "evry monday",
        "nexxt tuesday",
    ]
    
    for test in fuzzy_tests:
        corrected = parser._apply_fuzzy_correction(test)
        print(f"Original: '{test}' -> Corrected: '{corrected}'")
    
    print("\n===== SUGGESTION TESTS =====\n")
    
    # Test suggestions
    suggestion_tests = [
        "3-5",
        "4pm-6",
        "next wek",
    ]
    
    for test in suggestion_tests:
        suggestion = parser.suggest_correction(test)
        print(f"Original: '{test}' -> Suggestion: '{suggestion}'")

if __name__ == "__main__":
    test_time_parser()
