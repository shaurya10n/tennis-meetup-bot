#!/usr/bin/env python3
"""Test script to verify automatic matchmaking functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.dynamodb_config import get_db
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.database.dao.dynamodb.match_dao import MatchDAO
from src.utils.matching_algorithm import TennisMatchingAlgorithm
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def test_automatic_matchmaking():
    """Test the automatic matchmaking functionality."""
    try:
        # Initialize DAOs
        db = get_db()
        schedule_dao = ScheduleDAO(db)
        player_dao = PlayerDAO(db)
        court_dao = CourtDAO(db)
        match_dao = MatchDAO(db)
        
        # Initialize matching algorithm
        matching_algorithm = TennisMatchingAlgorithm(
            player_dao, schedule_dao, court_dao, match_dao
        )
        
        # Test guild and user IDs
        guild_id = "1234567890123456789"
        user_id = "123456789"  # Use one of the seeded user IDs
        
        print(f"Testing automatic matchmaking for user {user_id} in guild {guild_id}")
        
        # Create a test schedule
        now = datetime.now(ZoneInfo("America/Vancouver"))
        start_time = int((now + timedelta(days=1, hours=14)).timestamp())  # Tomorrow 2 PM
        end_time = int((now + timedelta(days=1, hours=16)).timestamp())    # Tomorrow 4 PM
        
        print(f"Creating test schedule: {datetime.fromtimestamp(start_time)} - {datetime.fromtimestamp(end_time)}")
        
        # Create the schedule
        schedule = schedule_dao.create_schedule(
            guild_id=guild_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            status="open"
        )
        
        print(f"Created schedule with ID: {schedule.schedule_id}")
        
        # Test automatic matchmaking
        print("\nTesting automatic matchmaking...")
        suggestions = matching_algorithm.find_matches_for_schedule(guild_id, schedule.schedule_id)
        
        if not suggestions:
            print("No match suggestions found.")
            return
        
        print(f"Found {len(suggestions)} match suggestions:")
        
        # Filter valid suggestions (no existing matches)
        valid_suggestions = []
        for suggestion in suggestions:
            existing_matches = match_dao.get_matches_by_players_and_time(
                str(suggestion.guild_id),
                [p.user_id for p in suggestion.players],
                suggestion.suggested_time[0],
                suggestion.suggested_time[1]
            )
            
            if not existing_matches:
                valid_suggestions.append(suggestion)
        
        print(f"Found {len(valid_suggestions)} valid suggestions (no existing matches):")
        
        for i, suggestion in enumerate(valid_suggestions[:3], 1):
            print(f"\nMatch Suggestion {i}:")
            
            # Get player names
            player_names = [p.username for p in suggestion.players]
            if suggestion.match_type == "singles":
                match_text = f"{player_names[0]} vs {player_names[1]}"
            else:
                match_text = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
            
            print(f"  Players: {match_text}")
            print(f"  Type: {suggestion.match_type}")
            print(f"  Time: {datetime.fromtimestamp(suggestion.suggested_time[0])} - {datetime.fromtimestamp(suggestion.suggested_time[1])}")
            print(f"  Score: {suggestion.overall_score:.2f}/1.0")
            print(f"  Court: {suggestion.suggested_court.name if suggestion.suggested_court else 'TBD'}")
            print(f"  Reasons: {', '.join(suggestion.reasons[:2])}")
        
        # Clean up - delete the test schedule
        print(f"\nCleaning up test schedule {schedule.schedule_id}...")
        schedule_dao.delete_schedule(guild_id, schedule.schedule_id)
        print("Test schedule deleted.")
        
    except Exception as e:
        print(f"Error testing automatic matchmaking: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_automatic_matchmaking() 