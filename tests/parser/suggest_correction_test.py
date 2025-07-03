"""Test for the suggest_correction functionality."""

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
    """Test the suggest_correction method with various inputs."""
    parser = TimeParser()
    
    # Test cases with expected corrections
    test_cases = [
        # Basic corrections
        ("3-5", "3-5pm"),  # Add pm to bare times
        ("4-6", "4-6pm"),
        
        # Missing meridiem
        ("4pm-6", "4pm-6pm"),  # Add missing pm to end time
        ("6am-8", "6am-8am"),  # Add missing am to end time
        
        # Spacing issues
        ("nextmonday", "next monday"),  # Fix spacing in relative dates
        ("everymonday", "every monday"),  # Fix spacing in recurrence
        
        # Number format issues
        ("1030-1130", "10:30-11:30"),  # Fix military time format
        ("0900-1000", "9:00-10:00"),
        
        # Typos in day names
        ("tommorow", "tomorrow"),
        ("tomorow", "tomorrow"),
        ("nexxt week", "next week"),
        
        # Typos in recurring patterns
        ("evry monday", "every monday"),
        ("every tuseday", "every tuesday"),
        
        # Missing context
        ("3pm", "today 3pm"),  # Add today context
        ("afternoon", "today afternoon"),
        
        # Complex corrections
        ("nxt wk tue 3-5", "next week tuesday 3-5pm"),  # Multiple corrections
        ("tmrw aftrn", "tomorrow afternoon"),  # Abbreviations
    ]
    
    print("\n===== SUGGEST CORRECTION TEST RESULTS =====\n")
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for i, (input_text, expected_correction) in enumerate(test_cases):
        print(f"Test {i+1}: '{input_text}'")
        suggested = parser.suggest_correction(input_text)
        
        if suggested is None:
            print(f"❌ FAILED: No suggestion provided")
            print(f"   Expected: '{expected_correction}'")
        elif suggested == expected_correction:
            print(f"✅ PASSED: Suggested '{suggested}'")
            
            # Verify the suggestion actually parses correctly
            start_time, end_time, error = parser.parse_time_description(suggested)
            if error:
                print(f"   ⚠️ Warning: Suggestion doesn't parse: {error}")
            else:
                print(f"   ✅ Suggestion parses correctly")
                print(f"      Start: {start_time}")
                print(f"      End: {end_time}")
                successful_tests += 1
        else:
            print(f"⚠️ DIFFERENT: Suggested '{suggested}' instead of '{expected_correction}'")
            
            # Check if the suggestion still parses correctly
            start_time, end_time, error = parser.parse_time_description(suggested)
            if error:
                print(f"   ❌ Suggestion doesn't parse: {error}")
            else:
                print(f"   ✅ Suggestion parses correctly")
                print(f"      Start: {start_time}")
                print(f"      End: {end_time}")
                successful_tests += 1
        
        print("")
    
    # Print summary
    print(f"Summary: {successful_tests}/{total_tests} tests passed")
    
    # Test fuzzy matching separately
    print("\n===== FUZZY MATCHING TEST =====\n")
    
    fuzzy_tests = [
        "tomorow",
        "nxt week",
        "evry monday",
        "nexxt tuesday",
        "wensday",
        "thurday",
    ]
    
    for test in fuzzy_tests:
        corrected = parser._apply_fuzzy_correction(test)
        print(f"Original: '{test}' -> Corrected: '{corrected}'")

if __name__ == "__main__":
    main()
