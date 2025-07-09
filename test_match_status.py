#!/usr/bin/env python3
"""Test script to verify match status checking functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.dynamodb_config import get_db
from src.database.dao.dynamodb.match_dao import MatchDAO
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.utils.matching_algorithm import TennisMatchingAlgorithm, MatchSuggestion

def test_match_status_checking():
    """Test the match status checking functionality."""
    try:
        # Initialize DAOs
        db = get_db()
        match_dao = MatchDAO(db)
        player_dao = PlayerDAO(db)
        schedule_dao = ScheduleDAO(db)
        court_dao = CourtDAO(db)
        
        # Initialize matching algorithm
        matching_algorithm = TennisMatchingAlgorithm(
            player_dao, schedule_dao, court_dao, match_dao
        )
        
        # Test guild and user IDs
        guild_id = "1234567890123456789"  # Replace with actual guild ID
        user_id = "123456789"  # Use one of the seeded user IDs
        
        print(f"Testing match status checking for user {user_id} in guild {guild_id}")
        
        # Find matches
        suggestions = matching_algorithm.find_matches_for_player(guild_id, user_id, hours_ahead=168)
        
        if not suggestions:
            print("No match suggestions found.")
            return
        
        print(f"Found {len(suggestions)} match suggestions:")
        
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"\nMatch Suggestion {i}:")
            
            # Get player names
            player_names = [p.username for p in suggestion.players]
            if suggestion.match_type == "singles":
                match_text = f"{player_names[0]} vs {player_names[1]}"
            else:
                match_text = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
            
            print(f"  Players: {match_text}")
            print(f"  Type: {suggestion.match_type}")
            print(f"  Time: {suggestion.suggested_time[0]} - {suggestion.suggested_time[1]}")
            print(f"  Score: {suggestion.overall_score:.2f}/1.0")
            
            # Test the new method
            existing_matches = match_dao.get_matches_by_players_and_time(
                str(suggestion.guild_id),
                [p.user_id for p in suggestion.players],
                suggestion.suggested_time[0],
                suggestion.suggested_time[1]
            )
            
            if existing_matches:
                print(f"  ✅ Found existing match with status: {existing_matches[0].status}")
                print(f"  Match ID: {existing_matches[0].match_id}")
            else:
                print(f"  ❌ No existing match found")
            
            print(f"  Reasons: {', '.join(suggestion.reasons[:2])}")
        
    except Exception as e:
        print(f"Error testing match status checking: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_match_status_checking() 