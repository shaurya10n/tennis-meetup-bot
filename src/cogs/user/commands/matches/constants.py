"""Constants for matches commands."""

# Command descriptions
MATCHES_VIEW_DESC = "View your completed or upcoming matches"
MATCHES_VIEW_COMPLETED_DESC = "View your completed matches"
MATCHES_VIEW_UPCOMING_DESC = "View your upcoming matches"
MATCHES_COMPLETE_DESC = "Complete a match and record results"

# Error messages
MATCH_NOT_FOUND = "Match not found. Please check the match ID and try again."
MATCH_ALREADY_COMPLETED = "This match has already been completed."
MATCH_NOT_SCHEDULED = "This match is not in a scheduled state and cannot be completed."
PLAYER_NOT_IN_MATCH = "You are not a player in this match."
INVALID_SCORE_FORMAT = "Invalid score format. Please use format like '6-4, 6-2' for singles or '6-4, 6-2, 6-4' for doubles."
INVALID_QUALITY_SCORE = "Match quality score must be between 1 and 10."

# Success messages
MATCH_COMPLETED_SUCCESS = "Match completed successfully! Results have been recorded."

# Embed colors
EMBED_COLOR_SCHEDULED = 0x3498db  # Blue
EMBED_COLOR_IN_PROGRESS = 0xf39c12  # Orange
EMBED_COLOR_COMPLETED = 0x27ae60  # Green
EMBED_COLOR_CANCELLED = 0xe74c3c  # Red 