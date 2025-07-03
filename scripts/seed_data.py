#!/usr/bin/env python3
"""
Seed script to populate DynamoDB tables with sample data for development.
"""

import os
import sys
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config.dynamodb_config import get_db
from src.database.init_db import init_database
from src.database.dao.dynamodb import PlayerDAO, ScheduleDAO, CourtDAO
from src.database.models.dynamodb.court import Court


def seed_courts(court_dao):
    """Seed sample courts using the existing court data."""
    print("Seeding courts...")
    
    # Sample court data from courts.json
    sample_courts = [
        {
            'court_id': 'kits-beach',
            'name': 'Kitsilano Beach Tennis Courts',
            'location': 'Kitsilano',
            'surface_type': 'hard',
            'number_of_courts': 6,
            'is_indoor': False,
            'amenities': ['lights', 'washroom', 'parking'],
            'google_maps_link': 'https://goo.gl/maps/your-kits-beach-link',
            'description': 'Public courts with beautiful beach view'
        },
        {
            'court_id': 'qe-park',
            'name': 'Queen Elizabeth Tennis Courts',
            'location': 'Queen Elizabeth Park',
            'surface_type': 'hard',
            'number_of_courts': 8,
            'is_indoor': False,
            'amenities': ['parking', 'washroom', 'water'],
            'google_maps_link': 'https://goo.gl/maps/your-qe-park-link',
            'description': 'Public courts in Queen Elizabeth Park'
        },
        {
            'court_id': 'ubc-tennis-centre',
            'name': 'UBC Tennis Centre',
            'location': 'UBC',
            'surface_type': 'hard',
            'number_of_courts': 12,
            'is_indoor': True,
            'amenities': ['lights', 'washroom', 'parking', 'pro_shop', 'seating'],
            'google_maps_link': 'https://goo.gl/maps/your-ubc-link',
            'description': 'Indoor tennis facility at UBC',
            'cost_per_hour': Decimal('30.0'),  # Using Decimal instead of float
            'booking_url': 'https://ubc-tennis-centre-booking-url'
        }
    ]
    
    # Create courts
    for court_data in sample_courts:
        court_id = court_data['court_id']
        name = court_data['name']
        location = court_data['location']
        surface_type = court_data['surface_type']
        number_of_courts = court_data['number_of_courts']
        is_indoor = court_data['is_indoor']
        amenities = court_data['amenities']
        google_maps_link = court_data['google_maps_link']
        
        court = Court(
            court_id=court_id,
            name=name,
            location=location,
            surface_type=surface_type,
            number_of_courts=number_of_courts,
            is_indoor=is_indoor,
            amenities=amenities,
            google_maps_link=google_maps_link,
            description=court_data.get('description'),
            cost_per_hour=court_data.get('cost_per_hour'),
            booking_url=court_data.get('booking_url')
        )
        
        court_dao.table.put_item(Item=court.to_dict())
    
    print(f"Created {len(sample_courts)} sample courts")
    return sample_courts


def seed_players(player_dao, courts):
    """Seed sample players."""
    print("Seeding players...")
    
    # Sample player data with correct interests from INTEREST_OPTIONS
    sample_players = [
        {
            'discord_id': '123456789',
            'username': 'JohnDoe',
            'ntrp_rating': Decimal('3.5'),  # Using Decimal instead of float
            'interests': ['regular_hits', 'matches'],
            'knows_ntrp': True,
            'preferred_locations': ['kits-beach', 'qe-park'],  # Using court_ids instead of location names
            'skill_level_preferences': ['similar', 'above'],
            'gender_preference': 'none'
        },
        {
            'discord_id': '987654321',
            'username': 'JaneSmith',
            'ntrp_rating': Decimal('4.0'),  # Using Decimal instead of float
            'interests': ['matches', 'coaching'],
            'knows_ntrp': True,
            'preferred_locations': ['ubc-tennis-centre'],  # Using court_ids instead of location names
            'skill_level_preferences': ['similar', 'below'],
            'gender_preference': 'women'
        },
        {
            'discord_id': '555555555',
            'username': 'SamJohnson',
            'ntrp_rating': Decimal('2.5'),  # Using Decimal instead of float
            'interests': ['regular_hits', 'social'],
            'knows_ntrp': False,
            'preferred_locations': ['kits-beach', 'ubc-tennis-centre'],  # Using court_ids instead of location names
            'skill_level_preferences': ['similar', 'any'],
            'gender_preference': 'men'
        }
    ]
    
    # Create players
    for player_data in sample_players:
        discord_id = player_data.pop('discord_id')
        username = player_data.pop('username')
        ntrp_rating = player_data.pop('ntrp_rating')
        interests = player_data.pop('interests')
        knows_ntrp = player_data.pop('knows_ntrp')
        
        player_dao.create_player(
            discord_id=discord_id,
            username=username,
            ntrp_rating=ntrp_rating,
            interests=interests,
            knows_ntrp=knows_ntrp,
            **player_data
        )
    
    print(f"Created {len(sample_players)} sample players")


def seed_schedules(schedule_dao):
    """Seed sample schedules."""
    print("Seeding schedules...")
    
    # Current time for reference
    now = int(datetime.now().timestamp())
    
    # Sample schedule data
    sample_schedules = [
        {
            'player_id': '123456789',
            'start_time': now + 86400,  # Tomorrow
            'end_time': now + 86400 + 7200,  # Tomorrow + 2 hours
            'use_profile_preferences': True
        },
        {
            'player_id': '123456789',
            'start_time': now + 259200,  # 3 days from now
            'end_time': now + 259200 + 5400,  # 3 days from now + 1.5 hours
            'location': 'qe-park',  # Using court_id instead of location name
            'skill_level_preference': ['similar'],
            'gender_preference': 'none',
            'use_profile_preferences': False,
            'recurrence': {
                'type': 'weekly',
                'days': ['monday', 'wednesday'],
                'until': now + 2592000  # 30 days from now
            }
        },
        {
            'player_id': '987654321',
            'start_time': now + 172800,  # 2 days from now
            'end_time': now + 172800 + 7200,  # 2 days from now + 2 hours
            'use_profile_preferences': True
        },
        {
            'player_id': '555555555',
            'start_time': now + 86400,  # Tomorrow
            'end_time': now + 86400 + 5400,  # Tomorrow + 1.5 hours
            'use_profile_preferences': True,
            'recurrence': {
                'type': 'daily',
                'until': now + 604800  # 7 days from now
            }
        }
    ]
    
    # Create schedules
    for schedule_data in sample_schedules:
        player_id = schedule_data.pop('player_id')
        start_time = schedule_data.pop('start_time')
        end_time = schedule_data.pop('end_time')
        
        try:
            schedule_dao.create_schedule(
                player_id=player_id,
                start_time=start_time,
                end_time=end_time,
                **schedule_data
            )
        except ValueError as e:
            print(f"Error creating schedule: {e}")
    
    print(f"Created {len(sample_schedules)} sample schedules")


def main():
    """Main function to seed the database."""
    print("Initializing database...")
    init_database()
    
    # Get DynamoDB resource
    dynamodb = get_db()
    
    # Create DAOs
    player_dao = PlayerDAO(dynamodb)
    court_dao = CourtDAO(dynamodb)
    schedule_dao = ScheduleDAO(dynamodb)
    
    # Seed data
    courts = seed_courts(court_dao)
    seed_players(player_dao, courts)
    seed_schedules(schedule_dao)
    
    print("Database seeding complete!")


if __name__ == "__main__":
    main()
