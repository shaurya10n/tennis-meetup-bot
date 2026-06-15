"""Unit tests for DynamoDB domain models."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.database.models.dynamodb.court import Court
from src.database.models.dynamodb.match import Match
from src.database.models.dynamodb.player import Player
from src.database.models.dynamodb.schedule import Schedule
from src.database.models.dynamodb.user_engagement import UserEngagement

from tests.conftest import future_timestamp, GUILD_ID


class TestPlayerModel:
    def test_to_dict_and_from_dict_roundtrip(self, sample_player):
        data = sample_player.to_dict()
        restored = Player.from_dict(data)
        assert restored.user_id == sample_player.user_id
        assert restored.ntrp_rating == sample_player.ntrp_rating

    def test_is_profile_complete_when_complete(self, sample_player):
        complete, missing = sample_player.is_profile_complete()
        assert complete is True
        assert missing == []

    def test_is_profile_complete_when_missing_fields(self):
        player = Player(
            guild_id=GUILD_ID,
            user_id="incomplete",
            username="New",
            dob="",
            gender="",
            ntrp_rating=None,
            knows_ntrp=False,
            interests=[],
            preferences={"locations": [], "skill_levels": [], "gender": ""},
        )
        complete, missing = player.is_profile_complete()
        assert complete is False
        assert len(missing) >= 4

    def test_can_update_rating_during_calibration(self, sample_player):
        future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        sample_player.calibration_ends_at = future
        can_update, reason = sample_player.can_update_rating()
        assert can_update is True
        assert "Calibration" in reason

    def test_can_update_rating_blocked_by_cooldown(self, sample_player):
        recent = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        sample_player.last_rating_update = recent
        can_update, reason = sample_player.can_update_rating()
        assert can_update is False
        assert "days" in reason

    def test_can_update_rating_allowed_after_cooldown(self, sample_player):
        old = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        sample_player.last_rating_update = old
        can_update, reason = sample_player.can_update_rating()
        assert can_update is True

    def test_create_table(self):
        dynamodb = MagicMock()
        Player.create_table(dynamodb)
        dynamodb.create_table.assert_called_once()


class TestScheduleModel:
    def test_to_dict_and_from_dict_roundtrip(self, sample_schedule):
        data = sample_schedule.to_dict()
        restored = Schedule.from_dict(data)
        assert restored.schedule_id == sample_schedule.schedule_id
        assert restored.start_time == sample_schedule.start_time

    def test_from_dict_converts_numeric_fields(self):
        data = {
            "guild_id": GUILD_ID,
            "user_id": "u1",
            "schedule_id": "s1",
            "start_time": "1700000000",
            "end_time": "1700007200",
            "recurrence": {"type": "weekly", "until": "1701000000"},
        }
        schedule = Schedule.from_dict(data)
        assert isinstance(schedule.start_time, int)
        assert isinstance(schedule.recurrence["until"], int)

    def test_overlaps_with_partial_overlap(self, sample_schedule, overlapping_schedule):
        assert sample_schedule.overlaps_with(overlapping_schedule) is True

    def test_overlaps_with_no_overlap(self, sample_schedule):
        start = future_timestamp(72)
        other = Schedule(
            guild_id=GUILD_ID,
            user_id="other",
            start_time=start,
            end_time=start + 3600,
        )
        assert sample_schedule.overlaps_with(other) is False

    def test_duration_minutes(self, sample_schedule):
        assert sample_schedule.duration_minutes() == 120

    def test_is_valid_rejects_past_schedule(self):
        past = int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp())
        schedule = Schedule(
            guild_id=GUILD_ID,
            user_id="u1",
            start_time=past,
            end_time=past + 3600,
        )
        valid, msg = schedule.is_valid()
        assert valid is False
        assert "past" in msg

    def test_is_valid_rejects_long_duration(self):
        start = future_timestamp(24)
        schedule = Schedule(
            guild_id=GUILD_ID,
            user_id="u1",
            start_time=start,
            end_time=start + 5 * 3600,
        )
        valid, msg = schedule.is_valid()
        assert valid is False
        assert "4 hours" in msg

    def test_is_valid_rejects_invalid_recurrence(self):
        start = future_timestamp(24)
        schedule = Schedule(
            guild_id=GUILD_ID,
            user_id="u1",
            start_time=start,
            end_time=start + 3600,
            recurrence="not-a-dict",
        )
        valid, msg = schedule.is_valid()
        assert valid is False

    def test_is_valid_accepts_future_schedule(self, sample_schedule):
        valid, msg = sample_schedule.is_valid()
        assert valid is True
        assert msg == ""

    def test_recurrence_type_flags(self, sample_schedule):
        assert sample_schedule.is_standalone() is True
        sample_schedule.recurrence = {"type": "weekly"}
        assert sample_schedule.is_recurring_parent() is True
        sample_schedule.parent_schedule_id = "parent-1"
        assert sample_schedule.is_recurring_instance() is True

    def test_get_next_occurrence_non_recurring_future(self, sample_schedule):
        after = int(datetime.now(timezone.utc).timestamp())
        assert sample_schedule.get_next_occurrence(after) == sample_schedule.start_time

    def test_get_next_occurrence_daily(self):
        start = future_timestamp(24)
        schedule = Schedule(
            guild_id=GUILD_ID,
            user_id="u1",
            start_time=start,
            end_time=start + 3600,
            recurrence={"type": "daily"},
        )
        after = start - 100
        next_occ = schedule.get_next_occurrence(after)
        assert next_occ is not None
        assert next_occ > after

    def test_get_next_occurrence_weekly(self):
        start = future_timestamp(24)
        schedule = Schedule(
            guild_id=GUILD_ID,
            user_id="u1",
            start_time=start,
            end_time=start + 3600,
            recurrence={"type": "weekly", "days": ["monday"]},
        )
        after = start - 100
        next_occ = schedule.get_next_occurrence(after)
        assert next_occ is not None

    def test_get_next_occurrence_monthly(self):
        start = future_timestamp(24)
        schedule = Schedule(
            guild_id=GUILD_ID,
            user_id="u1",
            start_time=start,
            end_time=start + 3600,
            recurrence={"type": "monthly"},
        )
        after = start - 100
        next_occ = schedule.get_next_occurrence(after)
        assert next_occ is not None

    def test_datetime_conversions(self, sample_schedule):
        ts = sample_schedule.start_time
        dt = sample_schedule.to_datetime(ts)
        assert dt.tzinfo == sample_schedule.timezone

    def test_get_next_occurrence_past_until(self):
        start = future_timestamp(24)
        until = start - 1000
        schedule = Schedule(
            guild_id=GUILD_ID,
            user_id="u1",
            start_time=start,
            end_time=start + 3600,
            recurrence={"type": "daily", "until": until},
        )
        assert schedule.get_next_occurrence(start + 5000) is None

    def test_is_valid_recurrence_type_and_until(self):
        start = future_timestamp(24)
        schedule = Schedule(
            guild_id=GUILD_ID,
            user_id="u1",
            start_time=start,
            end_time=start + 3600,
            recurrence={"type": "yearly"},
        )
        valid, msg = schedule.is_valid()
        assert valid is False
        assert "type" in msg

        schedule.recurrence = {"type": "weekly", "until": "bad"}
        valid, msg = schedule.is_valid()
        assert valid is False

    def test_to_dict_includes_optional_fields(self, sample_schedule):
        sample_schedule.parent_schedule_id = "parent"
        sample_schedule.recurrence = {"type": "weekly"}
        sample_schedule.match_id = "match-1"
        data = sample_schedule.to_dict()
        assert data["parent_schedule_id"] == "parent"
        assert data["recurrence"]["type"] == "weekly"
        assert data["match_id"] == "match-1"

    def test_from_datetime_adds_timezone_when_naive(self, sample_schedule):
        naive = datetime.now()
        ts = sample_schedule.from_datetime(naive)
        assert isinstance(ts, int)


class TestMatchModel:
    def test_to_dict_and_from_dict_roundtrip(self, sample_match):
        data = sample_match.to_dict()
        restored = Match.from_dict(data)
        assert restored.match_id == sample_match.match_id
        assert restored.players == sample_match.players

    def test_is_valid_singles_requires_two_players(self):
        match = Match(guild_id=GUILD_ID, players=["a"], match_type="singles")
        valid, msg = match.is_valid()
        assert valid is False
        assert "2 players" in msg

    def test_is_valid_doubles_requires_four_players(self):
        match = Match(
            guild_id=GUILD_ID,
            players=["a", "b", "c"],
            match_type="doubles",
        )
        valid, msg = match.is_valid()
        assert valid is False
        assert "4 players" in msg

    def test_is_valid_rejects_bad_status(self, sample_match):
        sample_match.status = "invalid"
        valid, msg = sample_match.is_valid()
        assert valid is False

    def test_player_management(self, sample_match):
        assert sample_match.is_player_in_match(sample_match.players[0]) is True
        assert sample_match.add_player("extra") is False
        assert sample_match.remove_player("missing") is False
        assert sample_match.remove_player(sample_match.players[0]) is True

    def test_match_lifecycle(self, sample_match):
        assert sample_match.can_start() is True
        assert sample_match.start_match() is True
        assert sample_match.status == "in_progress"
        assert sample_match.complete_match(
            sample_match.players[0], {"sets": "6-4"}, Decimal("8")
        ) is True
        assert sample_match.status == "completed"
        assert sample_match.get_duration_minutes() is not None

    def test_match_validation_and_optional_fields(self, sample_match):
        valid, _ = sample_match.is_valid()
        assert valid is True

        sample_match.start_time = sample_match.end_time + 100
        valid, msg = sample_match.is_valid()
        assert valid is False
        assert "after start" in msg

        data = sample_match.to_dict()
        assert "winner" not in data
        sample_match.winner = sample_match.players[0]
        sample_match.cancelled_reason = "rain"
        sample_match.notes = "great match"
        data = sample_match.to_dict()
        assert data["winner"] == sample_match.players[0]
        assert data["notes"] == "great match"

    def test_match_lifecycle_failures(self, sample_match):
        assert sample_match.start_match() is True
        assert sample_match.complete_match("not-a-player", {}) is False
        assert sample_match.can_start() is False

        doubles = Match(
            guild_id=GUILD_ID,
            players=["a", "b", "c", "d"],
            match_type="doubles",
            status="scheduled",
        )
        doubles.players = ["a", "b"]
        assert doubles.can_start() is False

    def test_create_table(self):
        dynamodb = MagicMock()
        Match.create_table(dynamodb)
        dynamodb.create_table.assert_called_once()


class TestCourtModel:
    def test_to_dict_and_from_dict_roundtrip(self, sample_court):
        data = sample_court.to_dict()
        restored = Court.from_dict(data)
        assert restored.court_id == sample_court.court_id
        assert restored.number_of_courts == sample_court.number_of_courts

    def test_from_dict_converts_types(self):
        data = {
            "court_id": "c1",
            "name": "Court",
            "location": "Downtown",
            "surface_type": "Clay",
            "number_of_courts": Decimal("3"),
            "is_indoor": False,
            "amenities": [],
            "google_maps_link": "http://example.com",
            "created_at": "1700000000",
            "updated_at": "1700000000",
        }
        court = Court.from_dict(data)
        assert isinstance(court.number_of_courts, int)
        assert isinstance(court.created_at, int)

    def test_create_table(self):
        dynamodb = MagicMock()
        Court.create_table(dynamodb)
        dynamodb.create_table.assert_called_once()


class TestUserEngagementModel:
    def test_to_dict_and_from_dict_roundtrip(self):
        engagement = UserEngagement(
            guild_id=GUILD_ID,
            discord_id="user-1",
            activity_type="message",
            details={"channel": "general"},
            engagement_value=Decimal("2.5"),
        )
        restored = UserEngagement.from_dict(engagement.to_dict())
        assert restored.activity_type == "message"
        assert restored.engagement_value == Decimal("2.5")

    def test_generates_engagement_id_when_missing(self):
        engagement = UserEngagement(
            guild_id=GUILD_ID,
            discord_id="user-1",
            activity_type="match",
        )
        assert engagement.engagement_id is not None

    def test_create_table(self):
        dynamodb = MagicMock()
        UserEngagement.create_table(dynamodb)
        dynamodb.create_table.assert_called_once()
