"""Shared pytest fixtures for tennis-meetup-bot tests."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.database.models.dynamodb.court import Court
from src.database.models.dynamodb.match import Match
from src.database.models.dynamodb.player import Player
from src.database.models.dynamodb.schedule import Schedule


GUILD_ID = "test-guild-123"


def future_timestamp(hours_from_now: int = 24) -> int:
    """Return a Unix timestamp in the future."""
    return int((datetime.now(timezone.utc) + timedelta(hours=hours_from_now)).timestamp())


@pytest.fixture
def sample_player_kwargs():
    return {
        "guild_id": GUILD_ID,
        "user_id": "user-1",
        "username": "Alice",
        "dob": "01/15/1990",
        "gender": "female",
        "ntrp_rating": Decimal("3.5"),
        "knows_ntrp": True,
        "interests": ["regular_hits", "matches"],
        "preferences": {
            "locations": ["kits-beach", "qe-park"],
            "skill_levels": ["similar", "above"],
            "gender": ["none"],
        },
        "engagement_score": Decimal("50"),
    }


@pytest.fixture
def sample_player(sample_player_kwargs):
    return Player(**sample_player_kwargs)


@pytest.fixture
def sample_player_two():
    return Player(
        guild_id=GUILD_ID,
        user_id="user-2",
        username="Bob",
        dob="03/22/1985",
        gender="male",
        ntrp_rating=Decimal("4.0"),
        knows_ntrp=True,
        interests=["matches"],
        preferences={
            "locations": ["kits-beach"],
            "skill_levels": ["similar", "below"],
            "gender": ["women"],
        },
        engagement_score=Decimal("80"),
    )


@pytest.fixture
def sample_schedule(sample_player):
    start = future_timestamp(24)
    return Schedule(
        guild_id=GUILD_ID,
        user_id=sample_player.user_id,
        start_time=start,
        end_time=start + 7200,
    )


@pytest.fixture
def overlapping_schedule(sample_player_two):
    start = future_timestamp(25)
    return Schedule(
        guild_id=GUILD_ID,
        user_id=sample_player_two.user_id,
        start_time=start,
        end_time=start + 7200,
    )


@pytest.fixture
def sample_court():
    return Court(
        court_id="kits-beach",
        name="Kitsilano Beach Tennis Courts",
        location="Kitsilano",
        surface_type="Hard",
        number_of_courts=4,
        is_indoor=False,
        amenities=["Parking"],
        google_maps_link="https://maps.google.com/kits-beach",
    )


@pytest.fixture
def sample_match(sample_player, sample_player_two):
    start = future_timestamp(24)
    return Match(
        guild_id=GUILD_ID,
        players=[sample_player.user_id, sample_player_two.user_id],
        match_type="singles",
        status="scheduled",
        start_time=start,
        end_time=start + 5400,
        match_quality_score=Decimal("8"),
    )


@pytest.fixture
def mock_dynamodb_table():
    table = MagicMock()
    table.put_item = MagicMock()
    table.get_item = MagicMock(return_value={"Item": None})
    table.update_item = MagicMock()
    table.delete_item = MagicMock(return_value={})
    table.scan = MagicMock(return_value={"Items": []})
    table.query = MagicMock(return_value={"Items": []})
    return table


@pytest.fixture
def mock_dynamodb(mock_dynamodb_table):
    dynamodb = MagicMock()
    dynamodb.Table.return_value = mock_dynamodb_table
    return dynamodb
