"""Unit tests for the schedule NLP time parser."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.cogs.user.commands.schedule.parser.nlp_parser import TimeParser


@pytest.fixture
def parser():
    return TimeParser()


class TestTimeParserBasics:
    @pytest.mark.parametrize(
        "description",
        [
            "tomorrow 4-6pm",
            "next monday 2-4pm",
            "next week tuesday 3-5pm",
            "every monday 4-6pm",
            "next two weeks 3pm to 5pm",
            "rest of the week 4-5 pm",
            "tomorrow afternoon",
            "next friday evening",
        ],
    )
    def test_valid_descriptions_parse(self, parser, description):
        start, end, error = parser.parse_time_description(description)
        assert error == ""
        assert start is not None
        assert end is not None
        assert end > start

    @pytest.mark.parametrize(
        "description",
        ["invalid time", ""],
    )
    def test_invalid_descriptions_fail(self, parser, description):
        start, end, error = parser.parse_time_description(description)
        assert start is None
        assert end is None
        assert error != ""

    def test_fuzzy_correction_fixes_typos(self, parser):
        corrected = parser._apply_fuzzy_correction("tomorow 3-5pm")
        assert "tomorrow" in corrected

    def test_extract_recurrence_patterns(self, parser):
        assert parser._extract_recurrence_pattern("every day 4-5pm") == ("daily", "day")
        assert parser._extract_recurrence_pattern("every monday 4-5pm")[0] == "weekly"
        assert parser._extract_recurrence_pattern("every week 4-5pm") == ("weekly", "week")
        assert parser._extract_recurrence_pattern("every month 4-5pm") == ("monthly", "month")
        assert parser._extract_recurrence_pattern("tomorrow 4-5pm") is None

    def test_suggest_correction_adds_meridiem(self, parser):
        suggestion = parser.suggest_correction("3-5")
        assert suggestion is not None
        assert "pm" in suggestion.lower()

    def test_suggest_correction_expands_abbreviations(self, parser):
        suggestion = parser.suggest_correction("tmrw 4-5pm")
        assert suggestion is not None
        assert "tomorrow" in suggestion

    def test_parse_rejects_duration_over_four_hours(self, parser):
        start, end, error = parser.parse_time_description("tomorrow 1pm-6pm")
        assert start is None
        assert "4 hours" in error

    def test_parse_rejects_end_before_start(self, parser):
        with patch.object(parser, "_process_time_range") as mock_range:
            now = datetime.now(parser.timezone) + timedelta(days=1)
            mock_range.return_value = (
                now.replace(hour=18),
                now.replace(hour=16),
                "",
            )
            start, end, error = parser.parse_time_description("tomorrow 6-4pm")
            assert start is None
            assert "after start" in error

    def test_parse_rejects_past_time(self, parser):
        with patch.object(parser, "_process_time_range") as mock_range:
            past = datetime.now(parser.timezone) - timedelta(hours=2)
            mock_range.return_value = (past, past + timedelta(hours=1), "")
            start, end, error = parser.parse_time_description("today 4-5pm")
            assert start is None
            assert "past" in error

    def test_parse_rejects_duration_under_thirty_minutes(self, parser):
        with patch.object(parser, "_process_time_range") as mock_range:
            now = datetime.now(parser.timezone) + timedelta(days=1)
            mock_range.return_value = (now, now + timedelta(minutes=15), "")
            start, end, error = parser.parse_time_description("tomorrow 4-4:15pm")
            assert start is None
            assert "30 minutes" in error

    def test_special_date_patterns(self, parser):
        now = datetime.now(parser.timezone).replace(hour=0, minute=0, second=0, microsecond=0)
        assert parser._parse_special_date_patterns("next 3 days") == now + timedelta(days=3)
        assert parser._parse_special_date_patterns("rest of the week") == now
        assert parser._parse_special_date_patterns("this week") == now
        assert parser._parse_special_date_patterns("next week") == now + timedelta(days=7)

    def test_next_week_day_pattern(self, parser):
        result = parser._parse_special_date_patterns("next week tuesday")
        assert result is not None
        assert result.weekday() == 1

    def test_day_abbreviation_in_time_range_error(self, parser):
        with patch.object(parser, "_parse_special_date_patterns", return_value=None):
            with patch("src.cogs.user.commands.schedule.parser.nlp_parser.dateparser.parse", return_value=None):
                start, end, error = parser.parse_time_description("mon 4-5pm")
                assert start is None
                assert "monday" in error.lower()

    def test_try_alternative_parsing_with_time_only(self, parser):
        start, end, error = parser._try_alternative_parsing("4pm")
        assert error == ""
        assert start is not None
        assert end is not None

    def test_parse_handles_unexpected_exception(self, parser):
        with patch.object(parser, "_apply_fuzzy_correction", side_effect=RuntimeError("boom")):
            start, end, error = parser.parse_time_description("tomorrow 4-5pm")
            assert start is None
            assert "Error parsing" in error

    def test_suggest_correction_handles_exception(self, parser):
        with patch("src.cogs.user.commands.schedule.parser.nlp_parser.re.sub", side_effect=RuntimeError("boom")):
            assert parser.suggest_correction("3-5") is None

    def test_weekly_recurrence_rewrites_description(self, parser):
        start, end, error = parser.parse_time_description("every thursday 4-5pm")
        assert error == ""
        assert start is not None

    def test_parse_special_patterns_time_of_day(self, parser):
        for phrase in ["tomorrow morning", "tomorrow afternoon", "tomorrow evening", "tomorrow night"]:
            start, end, error = parser.parse_time_description(phrase)
            assert error == ""
            assert end > start

    def test_parse_suggestion_on_time_range_error(self, parser):
        with patch.object(parser, "_process_time_range", return_value=(None, None, "bad range")):
            with patch.object(parser, "suggest_correction", return_value="tomorrow 4-5pm"):
                start, end, error = parser.parse_time_description("tomorow 4-5")
                assert start is None
                assert "Did you mean" in error

    def test_next_weeks_text_numbers(self, parser):
        now = datetime.now(parser.timezone).replace(hour=0, minute=0, second=0, microsecond=0)
        assert parser._parse_special_date_patterns("next two weeks") == now + timedelta(days=14)
        assert parser._parse_special_date_patterns("next three weeks") == now + timedelta(days=21)
        assert parser._parse_special_date_patterns("next four weeks") == now + timedelta(days=28)

    def test_weekend_on_saturday(self, parser):
        now = datetime.now(parser.timezone).replace(hour=0, minute=0, second=0, microsecond=0)
        if now.weekday() == 5:
            assert parser._parse_special_date_patterns("weekend") == now
