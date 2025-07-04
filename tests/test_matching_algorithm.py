"""Test script for the tennis matching algorithm."""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.database.dao.dynamodb.match_dao import MatchDAO
from src.config.dynamodb_config import get_db
from src.utils.matching_algorithm import TennisMatchingAlgorithm


def create_test_data():
    """Create test data for the matching algorithm."""
    db = get_db()
    player_dao = PlayerDAO(db)
    court_dao = CourtDAO(db)
    schedule_dao = ScheduleDAO(db)
    
    # Create test courts
    courts = [
        {
            'court_id': 'kits-beach',
            'name': 'Kitsilano Beach Tennis Courts',
            'location': 'Kitsilano',
            'surface_type': 'Hard',
            'number_of_courts': 4,
            'is_indoor': False,
            'amenities': ['Parking', 'Restrooms', 'Water'],
            'google_maps_link': 'https://maps.google.com/kits-beach'
        },
        {
            'court_id': 'qe-park',
            'name': 'Queen Elizabeth Park Tennis Courts',
            'location': 'Cambie',
            'surface_type': 'Hard',
            'number_of_courts': 6,
            'is_indoor': False,
            'amenities': ['Parking', 'Restrooms', 'Pro Shop'],
            'google_maps_link': 'https://maps.google.com/qe-park'
        },
        {
            'court_id': 'ubc-tennis-centre',
            'name': 'UBC Tennis Centre',
            'location': 'UBC',
            'surface_type': 'Hard',
            'number_of_courts': 8,
            'is_indoor': True,
            'amenities': ['Parking', 'Restrooms', 'Pro Shop', 'Cafe'],
            'google_maps_link': 'https://maps.google.com/ubc-tennis'
        }
    ]
    
    for court_data in courts:
        try:
            court_dao.create_court(**court_data)
            print(f"Created court: {court_data['name']}")
        except Exception as e:
            print(f"Court {court_data['name']} already exists or error: {e}")
    
    # Create test players
    players = [
        {
            'guild_id': 'test-guild',
            'user_id': 'player1',
            'username': 'Alice',
            'dob': '01/15/1990',
            'gender': 'female',
            'ntrp_rating': Decimal('3.5'),
            'knows_ntrp': True,
            'interests': ['regular_hits', 'matches'],
            'preferences': {
                'locations': ['kits-beach', 'qe-park'],
                'skill_levels': ['similar', 'above'],
                'gender': ['none']
            }
        },
        {
            'guild_id': 'test-guild',
            'user_id': 'player2',
            'username': 'Bob',
            'dob': '03/22/1985',
            'gender': 'male',
            'ntrp_rating': Decimal('4.0'),
            'knows_ntrp': True,
            'interests': ['matches', 'coaching'],
            'preferences': {
                'locations': ['ubc-tennis-centre'],
                'skill_levels': ['similar', 'below'],
                'gender': ['women']
            }
        },
        {
            'guild_id': 'test-guild',
            'user_id': 'player3',
            'username': 'Charlie',
            'dob': '07/10/1992',
            'gender': 'male',
            'ntrp_rating': Decimal('3.0'),
            'knows_ntrp': False,
            'interests': ['regular_hits', 'social'],
            'preferences': {
                'locations': ['kits-beach', 'ubc-tennis-centre'],
                'skill_levels': ['similar', 'any'],
                'gender': ['men']
            }
        },
        {
            'guild_id': 'test-guild',
            'user_id': 'player4',
            'username': 'Diana',
            'dob': '11/05/1988',
            'gender': 'female',
            'ntrp_rating': Decimal('3.8'),
            'knows_ntrp': True,
            'interests': ['matches', 'tournaments'],
            'preferences': {
                'locations': ['qe-park', 'ubc-tennis-centre'],
                'skill_levels': ['similar', 'above'],
                'gender': ['none']
            }
        }
    ]
    
    for player_data in players:
        try:
            player_dao.create_player(**player_data)
            print(f"Created player: {player_data['username']}")
        except Exception as e:
            print(f"Player {player_data['username']} already exists or error: {e}")
    
    # Create test schedules
    now = int(datetime.now().timestamp())
    schedules = [
        {
            'guild_id': 'test-guild',
            'user_id': 'player1',
            'start_time': now + 86400,  # Tomorrow
            'end_time': now + 86400 + 7200,  # Tomorrow + 2 hours
            'status': 'open'
        },
        {
            'guild_id': 'test-guild',
            'user_id': 'player2',
            'start_time': now + 86400 + 3600,  # Tomorrow + 1 hour
            'end_time': now + 86400 + 10800,  # Tomorrow + 3 hours
            'status': 'open'
        },
        {
            'guild_id': 'test-guild',
            'user_id': 'player3',
            'start_time': now + 86400,  # Tomorrow
            'end_time': now + 86400 + 5400,  # Tomorrow + 1.5 hours
            'status': 'open'
        },
        {
            'guild_id': 'test-guild',
            'user_id': 'player4',
            'start_time': now + 86400 + 1800,  # Tomorrow + 30 minutes
            'end_time': now + 86400 + 9000,  # Tomorrow + 2.5 hours
            'status': 'open'
        }
    ]
    
    for schedule_data in schedules:
        try:
            schedule_dao.create_schedule(**schedule_data)
            print(f"Created schedule for {schedule_data['user_id']}")
        except Exception as e:
            print(f"Schedule for {schedule_data['user_id']} already exists or error: {e}")


def test_matching_algorithm():
    """Test the matching algorithm with the test data."""
    db = get_db()
    player_dao = PlayerDAO(db)
    schedule_dao = ScheduleDAO(db)
    court_dao = CourtDAO(db)
    match_dao = MatchDAO(db)
    
    # Initialize the matching algorithm
    algorithm = TennisMatchingAlgorithm(player_dao, schedule_dao, court_dao, match_dao)
    
    print("\n" + "="*50)
    print("TESTING MATCHING ALGORITHM")
    print("="*50)
    
    # Test finding matches for each player
    test_players = ['player1', 'player2', 'player3', 'player4']
    
    for player_id in test_players:
        print(f"\n--- Finding matches for {player_id} ---")
        
        try:
            suggestions = algorithm.find_matches_for_player(
                guild_id='test-guild',
                user_id=player_id,
                hours_ahead=48  # 2 days
            )
            
            if suggestions:
                print(f"Found {len(suggestions)} match suggestions:")
                
                for i, suggestion in enumerate(suggestions[:3], 1):  # Show top 3
                    player_names = [p.username for p in suggestion.players]
                    if suggestion.match_type == "singles":
                        match_text = f"{player_names[0]} vs {player_names[1]}"
                    else:
                        match_text = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
                    
                    start_time = datetime.fromtimestamp(suggestion.suggested_time[0])
                    end_time = datetime.fromtimestamp(suggestion.suggested_time[1])
                    time_text = f"{start_time.strftime('%A, %B %d at %I:%M %p')} - {end_time.strftime('%I:%M %p')}"
                    
                    court_name = suggestion.suggested_court.name if suggestion.suggested_court else "TBD"
                    
                    print(f"  {i}. {match_text} ({suggestion.match_type.title()})")
                    print(f"     Time: {time_text}")
                    print(f"     Court: {court_name}")
                    print(f"     Score: {suggestion.overall_score:.2f}/1.0")
                    print(f"     Reasons: {', '.join(suggestion.reasons[:2])}")
                    print()
            else:
                print("No matches found.")
                
        except Exception as e:
            print(f"Error finding matches for {player_id}: {e}")


def test_compatibility_calculations():
    """Test individual compatibility calculations."""
    db = get_db()
    player_dao = PlayerDAO(db)
    schedule_dao = ScheduleDAO(db)
    court_dao = CourtDAO(db)
    match_dao = MatchDAO(db)
    
    algorithm = TennisMatchingAlgorithm(player_dao, schedule_dao, court_dao, match_dao)
    
    print("\n" + "="*50)
    print("TESTING COMPATIBILITY CALCULATIONS")
    print("="*50)
    
    # Get test players
    player1 = player_dao.get_player('test-guild', 'player1')
    player2 = player_dao.get_player('test-guild', 'player2')
    
    if player1 and player2:
        # Get their schedules
        schedules1 = schedule_dao.get_user_schedules('test-guild', 'player1')
        schedules2 = schedule_dao.get_user_schedules('test-guild', 'player2')
        
        if schedules1 and schedules2:
            # Test compatibility calculation
            compatibility = algorithm._calculate_compatibility(
                player1, player2, schedules1[0], schedules2[0]
            )
            
            print(f"\nCompatibility between {player1.username} and {player2.username}:")
            print(f"  Overall Score: {compatibility['overall_score']:.3f}")
            print(f"  NTRP Compatibility: {compatibility['ntrp_compatibility']:.3f}")
            print(f"  Skill Compatibility: {compatibility['skill_compatibility']:.3f}")
            print(f"  Gender Compatibility: {compatibility['gender_compatibility']:.3f}")
            print(f"  Location Compatibility: {compatibility['location_compatibility']:.3f}")
            print(f"  Time Overlap: {compatibility['time_overlap']:.3f}")
            print(f"  Engagement Bonus: {compatibility['engagement_bonus']:.3f}")
            print(f"  Match History: {compatibility['match_history']:.3f}")
            print(f"  Reasons: {', '.join(compatibility['reasons'])}")


def main():
    """Main test function."""
    print("Tennis Matching Algorithm Test")
    print("="*50)
    
    # Create test data
    print("\nCreating test data...")
    create_test_data()
    
    # Test compatibility calculations
    test_compatibility_calculations()
    
    # Test the full matching algorithm
    test_matching_algorithm()
    
    print("\n" + "="*50)
    print("TEST COMPLETE")
    print("="*50)


if __name__ == "__main__":
    main() 