"""Constants for the find-matches command."""

# Command descriptions
FIND_MATCHES_DESC = "Find potential tennis matches based on your preferences and availability"
FIND_MATCHES_FOR_SCHEDULE_DESC = "Find matches for a specific schedule"

# Parameter descriptions
HOURS_AHEAD_DESC = "Number of hours to look ahead for matches (1-720, default: 168 = 1 week)"
SCHEDULE_ID_DESC = "ID of the schedule to find matches for"

# Error messages
ERRORS = {
    "PROFILE_REQUIRED": "You need to complete your profile first. Use `/get-started` to set up your profile.",
    "INCOMPLETE_PROFILE": "Please complete your profile first. Missing: {missing_fields}\n\nUse `/update-profile` to complete your profile.",
    "NO_SCHEDULES": "You don't have any schedules set up. Use `/schedule add` to add your availability first.",
    "INVALID_TIME_RANGE": "Please specify a time range between 1 hour and 30 days (720 hours).",
    "SCHEDULE_NOT_FOUND": "The specified schedule was not found.",
    "ACCESS_DENIED": "You can only find matches for your own schedules.",
    "NO_MATCHES_FOUND": "No suitable matches found in the next {hours_ahead} hours.",
    "NO_MATCHES_FOR_SCHEDULE": "No suitable matches found for this schedule.",
    "MATCH_CREATION_FAILED": "An error occurred while creating the match. Please try again.",
    "GENERAL_ERROR": "An error occurred. Please try again."
}

# Success messages
SUCCESS = {
    "MATCH_CREATED": "Your match has been successfully created and scheduled.",
    "PLAYERS_NOTIFIED": "All players have been notified of the match."
}

# Embed titles
EMBEDS = {
    "FINDING_MATCHES": "🔍 Finding Matches",
    "MATCH_SUGGESTIONS": "🎾 Match Suggestions",
    "NO_MATCHES": "❌ No Matches Found",
    "MATCH_CREATED": "🎾 Match Created!",
    "NO_MORE_MATCHES": "❌ No More Matches",
    "DETAILED_INFO": "📋 Detailed Match Information"
}

# Button labels
BUTTONS = {
    "PREVIOUS": "◀️ Previous",
    "NEXT": "Next ▶️",
    "ACCEPT": "✅ Accept Match",
    "DECLINE": "❌ Decline",
    "VIEW_DETAILS": "📋 View Details"
}

# Time ranges
TIME_RANGES = {
    "DEFAULT": 168,  # 1 week
    "MIN": 1,        # 1 hour
    "MAX": 720       # 30 days
}

# Match types
MATCH_TYPES = {
    "SINGLES": "singles",
    "DOUBLES": "doubles"
}

# Match statuses
MATCH_STATUSES = {
    "SCHEDULED": "scheduled",
    "IN_PROGRESS": "in_progress",
    "COMPLETED": "completed",
    "CANCELLED": "cancelled"
}

# Compatibility score thresholds
SCORE_THRESHOLDS = {
    "MINIMUM_SINGLES": 0.3,
    "MINIMUM_DOUBLES": 0.25,
    "EXCELLENT": 0.8,
    "GOOD": 0.6
}

# Default match duration (minutes)
DEFAULT_MATCH_DURATION = 90

# Warm-up time (minutes)
WARM_UP_TIME = 15

# View timeout (seconds)
VIEW_TIMEOUT = 300  # 5 minutes

# Maximum suggestions to show
MAX_SUGGESTIONS_DISPLAY = 5

# Maximum reasons to show in summary
MAX_REASONS_SUMMARY = 3 