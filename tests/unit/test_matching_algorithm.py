"""Unit tests for the tennis matching algorithm."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.database.models.dynamodb.match import Match
from src.database.models.dynamodb.player import Player
from src.database.models.dynamodb.schedule import Schedule
from src.utils.matching_algorithm import TennisMatchingAlgorithm

from tests.conftest import future_timestamp, GUILD_ID


@pytest.fixture
def mock_daos(sample_player, sample_player_two, sample_schedule, overlapping_schedule, sample_court):
    player_dao = MagicMock()
    schedule_dao = MagicMock()
    court_dao = MagicMock()
    match_dao = MagicMock()

    players = {
        sample_player.user_id: sample_player,
        sample_player_two.user_id: sample_player_two,
    }
    player_dao.get_player.side_effect = lambda guild_id, user_id: players.get(str(user_id))

    schedule_dao.get_user_schedules.return_value = [sample_schedule]
    schedule_dao.get_schedule.return_value = sample_schedule
    schedule_dao.get_overlapping_schedules.return_value = [overlapping_schedule]

    court_dao.get_court.return_value = sample_court
    court_dao.list_courts.return_value = [sample_court]

    match_dao.get_player_matches.return_value = []
    match_dao.get_existing_match_status.return_value = None

    return player_dao, schedule_dao, court_dao, match_dao


@pytest.fixture
def algorithm(mock_daos):
    return TennisMatchingAlgorithm(*mock_daos)


class TestMatchingAlgorithmEntryPoints:
    def test_find_matches_player_not_found(self, algorithm, mock_daos):
        player_dao, _, _, _ = mock_daos
        player_dao.get_player.return_value = None
        assert algorithm.find_matches_for_player(GUILD_ID, "missing") == []

    def test_find_matches_no_schedules(self, algorithm, mock_daos, sample_player):
        _, schedule_dao, _, _ = mock_daos
        schedule_dao.get_user_schedules.return_value = []
        assert algorithm.find_matches_for_player(GUILD_ID, sample_player.user_id) == []

    def test_find_matches_no_available_opponents(self, algorithm, mock_daos, sample_player):
        _, schedule_dao, _, _ = mock_daos
        schedule_dao.get_overlapping_schedules.return_value = []
        assert algorithm.find_matches_for_player(GUILD_ID, sample_player.user_id) == []

    def test_find_matches_returns_suggestions(
        self, algorithm, sample_player, sample_player_two
    ):
        suggestions = algorithm.find_matches_for_player(GUILD_ID, sample_player.user_id)
        assert len(suggestions) >= 1
        assert suggestions[0].match_type == "singles"
        assert len(suggestions[0].players) == 2

    def test_find_matches_for_schedule_not_found(self, algorithm, mock_daos):
        _, schedule_dao, _, _ = mock_daos
        schedule_dao.get_schedule.return_value = None
        assert algorithm.find_matches_for_schedule(GUILD_ID, "missing") == []

    def test_find_matches_for_schedule_player_not_found(
        self, algorithm, mock_daos, sample_schedule
    ):
        player_dao, schedule_dao, _, _ = mock_daos
        schedule_dao.get_schedule.return_value = sample_schedule
        player_dao.get_player.side_effect = None
        player_dao.get_player.return_value = None
        assert algorithm.find_matches_for_schedule(GUILD_ID, sample_schedule.schedule_id) == []

    def test_find_matches_for_schedule_no_overlapping(
        self, algorithm, mock_daos, sample_schedule
    ):
        _, schedule_dao, _, _ = mock_daos
        schedule_dao.get_overlapping_schedules.return_value = []
        assert algorithm.find_matches_for_schedule(GUILD_ID, sample_schedule.schedule_id) == []

    def test_find_matches_for_schedule_handles_exceptions(
        self, algorithm, mock_daos, sample_schedule
    ):
        _, schedule_dao, _, _ = mock_daos
        schedule_dao.get_schedule.side_effect = RuntimeError("db down")
        assert algorithm.find_matches_for_schedule(GUILD_ID, sample_schedule.schedule_id) == []

    def test_find_matches_handles_exceptions(self, algorithm, mock_daos, sample_player):
        player_dao, _, _, _ = mock_daos
        player_dao.get_player.side_effect = RuntimeError("db down")
        assert algorithm.find_matches_for_player(GUILD_ID, sample_player.user_id) == []


class TestCompatibilityCalculations:
    def test_ntrp_compatibility_thresholds(self, algorithm):
        assert algorithm._calculate_ntrp_compatibility(0.3) == 1.0
        assert algorithm._calculate_ntrp_compatibility(0.8) == 0.8
        assert algorithm._calculate_ntrp_compatibility(1.2) == 0.6
        assert algorithm._calculate_ntrp_compatibility(1.8) == 0.3
        assert algorithm._calculate_ntrp_compatibility(3.0) == 0.0

    def test_skill_preference_any_and_similar(
        self, algorithm, sample_player, sample_player_two, sample_schedule, overlapping_schedule
    ):
        sample_player.preferences["skill_levels"] = ["any"]
        sample_player_two.preferences["skill_levels"] = ["similar"]
        score = algorithm._calculate_skill_preference_compatibility(
            sample_player, sample_player_two
        )
        assert 0 < score <= 1.0

    def test_skill_preference_above_and_below(
        self, algorithm, sample_player, sample_player_two
    ):
        sample_player.preferences["skill_levels"] = ["above"]
        sample_player_two.preferences["skill_levels"] = ["below"]
        score = algorithm._calculate_skill_preference_compatibility(
            sample_player, sample_player_two
        )
        assert score == 1.0

    def test_gender_compatibility_none_preference(
        self, algorithm, sample_player, sample_player_two
    ):
        sample_player.preferences["gender"] = ["none"]
        assert algorithm._calculate_gender_compatibility(sample_player, sample_player_two) == 1.0

        sample_player.preferences["gender"] = ["women"]
        sample_player_two.preferences["gender"] = ["none"]
        assert algorithm._calculate_gender_compatibility(sample_player, sample_player_two) == 1.0

    def test_gender_compatibility_no_match_when_preferences_conflict(
        self, algorithm, sample_player, sample_player_two
    ):
        sample_player.gender = "female"
        sample_player_two.gender = "male"
        sample_player.preferences["gender"] = ["women"]
        sample_player_two.preferences["gender"] = ["women"]
        assert algorithm._calculate_gender_compatibility(sample_player, sample_player_two) == 0.0

    def test_location_compatibility(
        self, algorithm, sample_player, sample_player_two, sample_schedule, overlapping_schedule
    ):
        assert algorithm._calculate_location_compatibility(
            sample_player, sample_player_two, sample_schedule, overlapping_schedule
        ) == 1.0

        sample_player_two.preferences["locations"] = ["other-court"]
        assert algorithm._calculate_location_compatibility(
            sample_player, sample_player_two, sample_schedule, overlapping_schedule
        ) == 0.0

        sample_player.preferences["locations"] = []
        assert algorithm._calculate_location_compatibility(
            sample_player, sample_player_two, sample_schedule, overlapping_schedule
        ) == 0.5

    def test_time_overlap(self, algorithm, sample_schedule, overlapping_schedule):
        overlap = algorithm._calculate_time_overlap(sample_schedule, overlapping_schedule)
        assert 0 < overlap <= 1.0

        non_overlapping = Schedule(
            guild_id=GUILD_ID,
            user_id="x",
            start_time=sample_schedule.end_time + 3600,
            end_time=sample_schedule.end_time + 7200,
        )
        assert algorithm._calculate_time_overlap(sample_schedule, non_overlapping) == 0.0

    def test_engagement_bonus(self, algorithm, sample_player, sample_player_two):
        bonus = algorithm._calculate_engagement_bonus(sample_player, sample_player_two)
        assert 0 < bonus <= 1.0

    def test_match_history_high_quality(
        self, algorithm, mock_daos, sample_player, sample_player_two
    ):
        _, _, _, match_dao = mock_daos
        past_match = Match(
            guild_id=GUILD_ID,
            players=[sample_player.user_id, sample_player_two.user_id],
            match_type="singles",
            status="completed",
            match_quality_score=Decimal("8"),
        )
        match_dao.get_player_matches.return_value = [past_match]
        factor = algorithm._calculate_match_history_factor(sample_player, sample_player_two)
        assert factor == 1.0

    def test_match_history_medium_quality(
        self, algorithm, mock_daos, sample_player, sample_player_two
    ):
        _, _, _, match_dao = mock_daos
        past_match = Match(
            guild_id=GUILD_ID,
            players=[sample_player.user_id, sample_player_two.user_id],
            match_type="singles",
            status="completed",
            match_quality_score=Decimal("6"),
        )
        match_dao.get_player_matches.return_value = [past_match]
        factor = algorithm._calculate_match_history_factor(sample_player, sample_player_two)
        assert factor == 0.5

    def test_full_compatibility_includes_reasons(
        self, algorithm, sample_player, sample_player_two, sample_schedule, overlapping_schedule
    ):
        result = algorithm._calculate_compatibility(
            sample_player, sample_player_two, sample_schedule, overlapping_schedule
        )
        assert "overall_score" in result
        assert result["overall_score"] > 0.3
        assert isinstance(result["reasons"], list)


class TestMatchSuggestionBuilding:
    def test_existing_match_status_adjustments(
        self, algorithm, mock_daos, sample_player, sample_player_two, sample_schedule, overlapping_schedule
    ):
        _, _, _, match_dao = mock_daos
        for status, multiplier in [
            ("scheduled", 0.8),
            ("pending_confirmation", 0.5),
            ("recently_cancelled", 0.3),
        ]:
            match_dao.get_existing_match_status.return_value = status
            suggestions = algorithm._find_singles_matches(
                sample_player,
                sample_schedule,
                [overlapping_schedule],
                {sample_player_two.user_id: sample_player_two},
            )
            assert suggestions
            base = algorithm._calculate_compatibility(
                sample_player, sample_player_two, sample_schedule, overlapping_schedule
            )["overall_score"]
            assert suggestions[0].overall_score == pytest.approx(base * multiplier, rel=0.01)

    def test_doubles_match_suggestion(
        self, algorithm, sample_player, sample_schedule, overlapping_schedule
    ):
        extra_players = []
        extra_schedules = []
        for i in range(3):
            uid = f"extra-{i}"
            extra_players.append(
                Player(
                    guild_id=GUILD_ID,
                    user_id=uid,
                    username=f"Player{i}",
                    dob="01/01/1990",
                    gender="male",
                    ntrp_rating=Decimal("3.5"),
                    knows_ntrp=True,
                    interests=["matches"],
                    preferences={
                        "locations": ["kits-beach"],
                        "skill_levels": ["any"],
                        "gender": ["none"],
                    },
                )
            )
            start = sample_schedule.start_time
            extra_schedules.append(
                Schedule(
                    guild_id=GUILD_ID,
                    user_id=uid,
                    start_time=start,
                    end_time=start + 7200,
                )
            )

        all_players = {p.user_id: p for p in extra_players}
        suggestions = algorithm._find_doubles_matches(
            sample_player, sample_schedule, extra_schedules, all_players
        )
        assert len(suggestions) == 1
        assert suggestions[0].match_type == "doubles"
        assert len(suggestions[0].players) == 4

    def test_group_compatibility_invalid_size(self, algorithm):
        result = algorithm._calculate_group_compatibility([], [])
        assert result["overall_score"] == 0.0

    def test_group_schedules_by_overlap(self, algorithm, sample_schedule, overlapping_schedule):
        groups = algorithm._group_schedules_by_overlap(
            sample_schedule, [overlapping_schedule]
        )
        assert len(groups) == 1
        assert overlapping_schedule in groups[0]

    def test_find_best_court_common_location(
        self, algorithm, mock_daos, sample_player, sample_player_two, sample_schedule, overlapping_schedule, sample_court
    ):
        court = algorithm._find_best_court(
            sample_player, sample_player_two, sample_schedule, overlapping_schedule
        )
        assert court.court_id == sample_court.court_id

    def test_find_best_court_fallback_to_list(
        self, algorithm, mock_daos, sample_player, sample_player_two, sample_schedule, overlapping_schedule, sample_court
    ):
        _, _, court_dao, _ = mock_daos
        sample_player.preferences["locations"] = ["nowhere"]
        sample_player_two.preferences["locations"] = ["elsewhere"]
        court_dao.get_court.return_value = None
        court = algorithm._find_best_court(
            sample_player, sample_player_two, sample_schedule, overlapping_schedule
        )
        assert court == sample_court

    def test_optimal_match_time_short_overlap(self, algorithm, sample_schedule):
        short = Schedule(
            guild_id=GUILD_ID,
            user_id="short",
            start_time=sample_schedule.start_time,
            end_time=sample_schedule.start_time + 45 * 60,
        )
        start, end = algorithm._find_optimal_match_time(sample_schedule, short)
        assert end - start == 45 * 60

    def test_optimal_group_match_time_empty(self, algorithm):
        assert algorithm._find_optimal_group_match_time([]) == (0, 0)

    def test_get_players_for_schedules(
        self, algorithm, mock_daos, sample_schedule, overlapping_schedule, sample_player, sample_player_two
    ):
        players = algorithm._get_players_for_schedules(
            GUILD_ID, [sample_schedule, overlapping_schedule]
        )
        assert sample_player.user_id in players
        assert sample_player_two.user_id in players

    def test_doubles_insufficient_players_returns_empty(
        self, algorithm, sample_player, sample_schedule, overlapping_schedule
    ):
        suggestions = algorithm._find_doubles_matches(
            sample_player,
            sample_schedule,
            [overlapping_schedule],
            {"user-2": sample_player},
        )
        assert suggestions == []

    def test_singles_skips_missing_player_and_self(
        self, algorithm, sample_player, sample_schedule, overlapping_schedule
    ):
        self_schedule = Schedule(
            guild_id=GUILD_ID,
            user_id=sample_player.user_id,
            start_time=sample_schedule.start_time,
            end_time=sample_schedule.end_time,
        )
        suggestions = algorithm._find_singles_matches(
            sample_player,
            sample_schedule,
            [self_schedule, overlapping_schedule],
            {},
        )
        assert suggestions == []

    def test_find_best_court_for_group_and_no_courts(
        self, algorithm, mock_daos, sample_player, sample_player_two, sample_schedule, sample_court
    ):
        _, _, court_dao, _ = mock_daos
        sample_player_two.preferences["locations"] = ["kits-beach"]
        players = [sample_player, sample_player_two]
        schedules = [sample_schedule, sample_schedule]
        court = algorithm._find_best_court_for_group(players, schedules)
        assert court.court_id == sample_court.court_id

        court_dao.list_courts.return_value = []
        sample_player.preferences["locations"] = []
        sample_player_two.preferences["locations"] = []
        assert algorithm._find_best_court_for_group(players, schedules) is None

    def test_compatibility_reason_branches(
        self, algorithm, sample_player, sample_player_two, sample_schedule, overlapping_schedule
    ):
        sample_player.ntrp_rating = Decimal("3.5")
        sample_player_two.ntrp_rating = Decimal("3.5")
        sample_player.preferences = {
            "locations": ["kits-beach"],
            "skill_levels": ["similar"],
            "gender": ["none"],
        }
        sample_player_two.preferences = sample_player.preferences.copy()
        sample_player.engagement_score = Decimal("90")
        sample_player_two.engagement_score = Decimal("90")
        result = algorithm._calculate_compatibility(
            sample_player, sample_player_two, sample_schedule, overlapping_schedule
        )
        assert any("skill" in reason.lower() for reason in result["reasons"])

    def test_skill_preference_below_branch(self, algorithm, sample_player, sample_player_two):
        sample_player.ntrp_rating = Decimal("4.0")
        sample_player_two.ntrp_rating = Decimal("3.0")
        sample_player.preferences["skill_levels"] = ["below"]
        sample_player_two.preferences["skill_levels"] = ["above"]
        assert algorithm._calculate_skill_preference_compatibility(
            sample_player, sample_player_two
        ) == 1.0

