"""Unit tests for DynamoDB DAOs."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.database.dao.dynamodb.court_dao import CourtDAO
from src.database.dao.dynamodb.match_dao import MatchDAO
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.database.dao.dynamodb.user_engagement_dao import UserEngagementDAO
from src.database.models.dynamodb.court import Court
from src.database.models.dynamodb.match import Match
from src.database.models.dynamodb.player import Player
from src.database.models.dynamodb.schedule import Schedule
from src.database.models.dynamodb.user_engagement import UserEngagement

from tests.conftest import future_timestamp, GUILD_ID


class TestPlayerDAO:
    def test_create_and_get_player(self, mock_dynamodb, mock_dynamodb_table, sample_player_kwargs):
        dao = PlayerDAO(mock_dynamodb)
        player = dao.create_player(
            guild_id=sample_player_kwargs["guild_id"],
            user_id=sample_player_kwargs["user_id"],
            username=sample_player_kwargs["username"],
            dob=sample_player_kwargs["dob"],
            gender=sample_player_kwargs["gender"],
            ntrp_rating=3.5,
            interests=sample_player_kwargs["interests"],
            knows_ntrp=True,
        )
        assert isinstance(player, Player)
        mock_dynamodb_table.put_item.assert_called_once()

        mock_dynamodb_table.get_item.return_value = {"Item": player.to_dict()}
        fetched = dao.get_player(player.guild_id, player.user_id)
        assert fetched.user_id == player.user_id

    def test_get_player_missing(self, mock_dynamodb, mock_dynamodb_table):
        dao = PlayerDAO(mock_dynamodb)
        assert dao.get_player(GUILD_ID, "missing") is None

    def test_update_player(self, mock_dynamodb, mock_dynamodb_table, sample_player):
        dao = PlayerDAO(mock_dynamodb)
        mock_dynamodb_table.get_item.return_value = {"Item": sample_player.to_dict()}
        updated = dao.update_player(GUILD_ID, sample_player.user_id, username="NewName")
        mock_dynamodb_table.update_item.assert_called_once()
        assert updated.username == sample_player.username

    def test_update_player_not_found(self, mock_dynamodb, mock_dynamodb_table):
        dao = PlayerDAO(mock_dynamodb)
        with pytest.raises(ValueError, match="not found"):
            dao.update_player(GUILD_ID, "missing", username="X")


class TestScheduleDAO:
    def test_create_schedule(self, mock_dynamodb, mock_dynamodb_table, sample_schedule):
        dao = ScheduleDAO(mock_dynamodb)
        start = future_timestamp(24)
        schedule = dao.create_schedule(
            guild_id=GUILD_ID,
            user_id="user-1",
            start_time=start,
            end_time=start + 7200,
        )
        assert isinstance(schedule, Schedule)
        mock_dynamodb_table.put_item.assert_called_once()

    def test_create_invalid_schedule_raises(self, mock_dynamodb):
        dao = ScheduleDAO(mock_dynamodb)
        past = int(datetime.now(timezone.utc).timestamp()) - 3600
        with pytest.raises(ValueError, match="Invalid schedule"):
            dao.create_schedule(
                guild_id=GUILD_ID,
                user_id="user-1",
                start_time=past,
                end_time=past + 3600,
            )

    def test_get_and_update_schedule(self, mock_dynamodb, mock_dynamodb_table, sample_schedule):
        dao = ScheduleDAO(mock_dynamodb)
        mock_dynamodb_table.get_item.return_value = {"Item": sample_schedule.to_dict()}
        fetched = dao.get_schedule(GUILD_ID, sample_schedule.schedule_id)
        assert fetched.schedule_id == sample_schedule.schedule_id

        updated = dao.update_schedule(
            GUILD_ID, sample_schedule.schedule_id, status="booked"
        )
        mock_dynamodb_table.update_item.assert_called_once()
        assert updated.schedule_id == sample_schedule.schedule_id

    def test_cancel_schedule(self, mock_dynamodb, mock_dynamodb_table, sample_schedule):
        dao = ScheduleDAO(mock_dynamodb)
        mock_dynamodb_table.get_item.return_value = {"Item": sample_schedule.to_dict()}
        assert dao.cancel_schedule(GUILD_ID, sample_schedule.schedule_id) is True

    def test_cancel_missing_schedule(self, mock_dynamodb, mock_dynamodb_table):
        dao = ScheduleDAO(mock_dynamodb)
        assert dao.cancel_schedule(GUILD_ID, "missing") is False

    def test_scan_and_query_helpers(self, mock_dynamodb, mock_dynamodb_table, sample_schedule):
        dao = ScheduleDAO(mock_dynamodb)
        item = sample_schedule.to_dict()
        mock_dynamodb_table.scan.return_value = {"Items": [item]}

        assert len(dao.get_user_schedules(GUILD_ID, sample_schedule.user_id)) == 1
        assert len(
            dao.get_user_schedules_in_time_range(
                GUILD_ID,
                sample_schedule.user_id,
                sample_schedule.start_time - 1,
                sample_schedule.end_time + 1,
            )
        ) == 1
        assert len(
            dao.get_overlapping_schedules(
                GUILD_ID,
                sample_schedule.start_time,
                sample_schedule.end_time,
            )
        ) == 1
        assert len(dao.get_schedules_by_location(GUILD_ID, "Downtown")) == 1

        mock_dynamodb_table.query.return_value = {"Items": [item]}
        start = sample_schedule.start_time
        end = sample_schedule.end_time
        assert len(dao.get_schedules_in_time_range(GUILD_ID, start, end)) >= 1

    def test_cancel_user_schedules(self, mock_dynamodb, mock_dynamodb_table, sample_schedule):
        dao = ScheduleDAO(mock_dynamodb)
        mock_dynamodb_table.get_item.return_value = {"Item": sample_schedule.to_dict()}
        mock_dynamodb_table.scan.return_value = {"Items": [sample_schedule.to_dict()]}
        count = dao.cancel_user_schedules(GUILD_ID, sample_schedule.user_id)
        assert count == 1

    def test_cancel_user_schedules_in_time_range(
        self, mock_dynamodb, mock_dynamodb_table, sample_schedule
    ):
        dao = ScheduleDAO(mock_dynamodb)
        mock_dynamodb_table.get_item.return_value = {"Item": sample_schedule.to_dict()}
        mock_dynamodb_table.scan.return_value = {"Items": [sample_schedule.to_dict()]}
        count = dao.cancel_user_schedules_in_time_range(
            GUILD_ID,
            sample_schedule.user_id,
            sample_schedule.start_time - 1,
            sample_schedule.end_time + 1,
        )
        assert count == 1


class TestCourtDAO:
    def test_create_and_get_court(self, mock_dynamodb, mock_dynamodb_table, sample_court):
        dao = CourtDAO(mock_dynamodb)
        created = dao.create_court(
            name=sample_court.name,
            location=sample_court.location,
            surface_type=sample_court.surface_type,
            number_of_courts=sample_court.number_of_courts,
            is_indoor=sample_court.is_indoor,
            amenities=sample_court.amenities,
            google_maps_link=sample_court.google_maps_link,
            court_id=sample_court.court_id,
        )
        assert isinstance(created, Court)
        mock_dynamodb_table.put_item.assert_called_once()

        mock_dynamodb_table.get_item.return_value = {"Item": created.to_dict()}
        fetched = dao.get_court(sample_court.court_id)
        assert fetched.court_id == sample_court.court_id

    def test_update_delete_and_list(self, mock_dynamodb, mock_dynamodb_table, sample_court):
        dao = CourtDAO(mock_dynamodb)
        mock_dynamodb_table.get_item.return_value = {"Item": sample_court.to_dict()}
        updated = dao.update_court(sample_court.court_id, name="Updated")
        assert updated.court_id == sample_court.court_id

        mock_dynamodb_table.delete_item.return_value = {"Attributes": sample_court.to_dict()}
        assert dao.delete_court(sample_court.court_id) is True

        mock_dynamodb_table.scan.return_value = {"Items": [sample_court.to_dict()]}
        assert len(dao.list_courts()) == 1

        mock_dynamodb_table.query.return_value = {"Items": [sample_court.to_dict()]}
        assert len(dao.get_courts_by_location(sample_court.location)) == 1
        assert len(dao.get_courts_by_attribute("is_indoor", False)) == 1

    def test_update_court_not_found(self, mock_dynamodb, mock_dynamodb_table):
        dao = CourtDAO(mock_dynamodb)
        with pytest.raises(ValueError, match="not found"):
            dao.update_court("missing", name="X")


class TestMatchDAO:
    def test_create_and_get_match(self, mock_dynamodb, mock_dynamodb_table, sample_match):
        dao = MatchDAO(mock_dynamodb)
        created = dao.create_match(
            guild_id=GUILD_ID,
            players=sample_match.players,
            match_type="singles",
            start_time=sample_match.start_time,
            end_time=sample_match.end_time,
        )
        assert isinstance(created, Match)
        mock_dynamodb_table.put_item.assert_called_once()

        mock_dynamodb_table.get_item.return_value = {"Item": created.to_dict()}
        assert dao.get_match(GUILD_ID, created.match_id).match_id == created.match_id

    def test_create_invalid_match_raises(self, mock_dynamodb):
        dao = MatchDAO(mock_dynamodb)
        with pytest.raises(ValueError, match="Invalid match"):
            dao.create_match(guild_id=GUILD_ID, players=["solo"], match_type="singles")

    def test_query_and_scan_helpers(self, mock_dynamodb, mock_dynamodb_table, sample_match):
        dao = MatchDAO(mock_dynamodb)
        item = sample_match.to_dict()
        mock_dynamodb_table.scan.return_value = {"Items": [item]}
        mock_dynamodb_table.query.return_value = {"Items": [item]}

        assert dao.get_match_by_id(sample_match.match_id) is not None
        assert len(dao.get_matches_by_schedule("sched-1")) == 1
        assert len(dao.get_matches_by_status(GUILD_ID, "scheduled")) == 1
        assert len(dao.get_matches_by_court("court-1")) == 1
        assert len(dao.get_player_matches(GUILD_ID, sample_match.players[0])) == 1
        assert len(dao.get_upcoming_matches(GUILD_ID)) == 1
        assert len(dao.get_matches_by_players(GUILD_ID, sample_match.players)) == 1
        assert len(
            dao.get_matches_by_players_and_time(
                GUILD_ID,
                sample_match.players,
                sample_match.start_time,
                sample_match.end_time,
            )
        ) == 1

    def test_get_existing_match_status_pending(self, mock_dynamodb, mock_dynamodb_table, sample_match):
        dao = MatchDAO(mock_dynamodb)
        pending = sample_match.to_dict()
        pending["status"] = "pending_confirmation"
        mock_dynamodb_table.scan.return_value = {"Items": [pending]}
        status = dao.get_existing_match_status(
            GUILD_ID,
            sample_match.players,
            sample_match.start_time,
            sample_match.end_time,
        )
        assert status == "pending_confirmation"
        assert dao.has_existing_match_request(
            GUILD_ID,
            sample_match.players,
            sample_match.start_time,
            sample_match.end_time,
        ) is True

    def test_get_existing_match_status_recently_cancelled(
        self, mock_dynamodb, mock_dynamodb_table, sample_match
    ):
        dao = MatchDAO(mock_dynamodb)
        cancelled = sample_match.to_dict()
        cancelled["status"] = "cancelled"
        cancelled["updated_at"] = datetime.now(timezone.utc).isoformat()
        mock_dynamodb_table.scan.return_value = {"Items": [cancelled]}
        assert dao.get_existing_match_status(
            GUILD_ID,
            sample_match.players,
            sample_match.start_time,
            sample_match.end_time,
        ) == "recently_cancelled"

    def test_update_and_delete_match(self, mock_dynamodb, mock_dynamodb_table, sample_match):
        dao = MatchDAO(mock_dynamodb)
        mock_dynamodb_table.get_item.return_value = {"Item": sample_match.to_dict()}
        updated = dao.update_match(GUILD_ID, sample_match.match_id, status="in_progress")
        assert updated.status == "in_progress"
        assert dao.delete_match(GUILD_ID, sample_match.match_id) is True

    def test_error_paths_return_empty_or_none(self, mock_dynamodb, mock_dynamodb_table):
        dao = MatchDAO(mock_dynamodb)
        mock_dynamodb_table.get_item.side_effect = RuntimeError("fail")
        assert dao.get_match(GUILD_ID, "x") is None

        mock_dynamodb_table.get_item.side_effect = None
        mock_dynamodb_table.get_item.return_value = {"Item": None}
    def test_query_error_paths(self, mock_dynamodb, mock_dynamodb_table):
        dao = MatchDAO(mock_dynamodb)
        mock_dynamodb_table.query.side_effect = RuntimeError("fail")
        assert dao.get_matches_by_schedule("sched-1") == []
        assert dao.get_matches_by_status(GUILD_ID, "scheduled") == []
        assert dao.get_matches_by_court("court-1") == []
        assert dao.get_upcoming_matches(GUILD_ID) == []

    def test_get_match_by_id_error(self, mock_dynamodb, mock_dynamodb_table):
        dao = MatchDAO(mock_dynamodb)
        mock_dynamodb_table.scan.side_effect = RuntimeError("fail")
        assert dao.get_match_by_id("match-1") is None

    def test_get_existing_match_status_bad_timestamp(
        self, mock_dynamodb, mock_dynamodb_table, sample_match
    ):
        dao = MatchDAO(mock_dynamodb)
        cancelled = sample_match.to_dict()
        cancelled["status"] = "cancelled"
        cancelled["updated_at"] = "not-a-timestamp"
        mock_dynamodb_table.scan.return_value = {"Items": [cancelled]}
        assert dao.get_existing_match_status(
            GUILD_ID,
            sample_match.players,
            sample_match.start_time,
            sample_match.end_time,
        ) == "recently_cancelled"

    def test_update_match_not_found_or_invalid(self, mock_dynamodb, mock_dynamodb_table, sample_match):
        dao = MatchDAO(mock_dynamodb)
        mock_dynamodb_table.get_item.return_value = {"Item": None}
        assert dao.update_match(GUILD_ID, "missing", status="completed") is None

        invalid = sample_match.to_dict()
        invalid["players"] = ["solo"]
        mock_dynamodb_table.get_item.side_effect = None
        mock_dynamodb_table.get_item.return_value = {"Item": invalid}
        assert dao.update_match(GUILD_ID, sample_match.match_id, players=["solo"]) is None

    def test_delete_match_error(self, mock_dynamodb, mock_dynamodb_table):
        dao = MatchDAO(mock_dynamodb)
        mock_dynamodb_table.delete_item.side_effect = RuntimeError("fail")
        assert dao.delete_match(GUILD_ID, "match-1") is False


class TestUserEngagementDAO:
    def test_create_and_get_engagement(self, mock_dynamodb, mock_dynamodb_table):
        dao = UserEngagementDAO(mock_dynamodb)
        engagement = dao.create_engagement(
            guild_id=GUILD_ID,
            discord_id="user-1",
            activity_type="message",
            details={"text": "hello"},
            engagement_value=2.0,
        )
        assert isinstance(engagement, UserEngagement)
        mock_dynamodb_table.put_item.assert_called_once()

        mock_dynamodb_table.get_item.return_value = {"Item": engagement.to_dict()}
        fetched = dao.get_engagement(GUILD_ID, engagement.engagement_id)
        assert fetched.discord_id == "user-1"

    def test_delete_and_list_engagements(self, mock_dynamodb, mock_dynamodb_table):
        dao = UserEngagementDAO(mock_dynamodb)
        engagement = UserEngagement(
            guild_id=GUILD_ID,
            discord_id="user-1",
            activity_type="match",
            engagement_value=Decimal("3"),
        )
        mock_dynamodb_table.delete_item.return_value = {"Attributes": engagement.to_dict()}
        assert dao.delete_engagement(GUILD_ID, engagement.engagement_id) is True

        mock_dynamodb_table.query.return_value = {"Items": [engagement.to_dict()]}
        assert len(dao.list_engagements_by_user(GUILD_ID, "user-1")) == 1
        assert len(dao.list_engagements_by_activity(GUILD_ID, "match")) == 1
    def test_list_engagements_with_time_filters(self, mock_dynamodb, mock_dynamodb_table):
        dao = UserEngagementDAO(mock_dynamodb)
        engagement = UserEngagement(
            guild_id=GUILD_ID,
            discord_id="user-1",
            activity_type="match",
            engagement_value=Decimal("3"),
        )
        mock_dynamodb_table.query.return_value = {"Items": [engagement.to_dict()]}
        assert (
            len(
                dao.list_engagements_by_user(
                    GUILD_ID,
                    "user-1",
                    start_time="2020-01-01",
                    end_time="2099-01-01",
                )
            )
            == 1
        )
        assert (
            len(
                dao.list_engagements_by_activity(
                    GUILD_ID,
                    "match",
                    start_time="2020-01-01",
                    end_time="2099-01-01",
                )
            )
            == 1
        )

    def test_get_engagement_missing(self, mock_dynamodb, mock_dynamodb_table):
        dao = UserEngagementDAO(mock_dynamodb)
        assert dao.get_engagement(GUILD_ID, "missing") is None
