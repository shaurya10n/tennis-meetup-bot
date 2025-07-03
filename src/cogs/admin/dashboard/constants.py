"""Constants for the availability dashboard."""

# Embed titles and descriptions
EMBEDS = {
    "DASHBOARD_TITLE": "Tennis Availability Dashboard",
    "LOCATION_TITLE": "Location Availability: {location}",
    "PLAYING_TITLE": "Currently Playing",
    "DASHBOARD_DESCRIPTION": "Player availability for the next 7 days",
    "LOCATION_DESCRIPTION": "Player availability at {location} for the next 7 days",
    "PLAYING_DESCRIPTION": "Players currently active based on schedules",
    "NO_DATA": "No availability data found for this period."
}

# Button labels
BUTTONS = {
    "PREVIOUS": "◀️ Previous",
    "NEXT": "Next ▶️",
    "REFRESH": "🔄 Refresh",
    "LOCATION_FILTER": "📍 Filter by Location",
    "VIEW_PLAYING": "🎾 View Playing Now"
}

# Time slots
TIME_SLOTS = {
    "Morning": (6, 12),    # 6am to 12pm
    "Afternoon": (12, 17), # 12pm to 5pm
    "Evening": (17, 22)    # 5pm to 10pm
}

# Date and time formats
DATE_FORMAT = "%A, %b %d"  # e.g., "Monday, May 1"
TIME_FORMAT = "%I:%M %p"   # e.g., "3:30 PM"

# Success messages
SUCCESS = {
    "DASHBOARD_POSTED": "Availability dashboard posted to {channel}.",
    "DASHBOARD_REFRESHED": "Availability dashboard refreshed."
}

# Error messages
ERRORS = {
    "NO_SCHEDULES": "No schedules found for the specified period.",
    "NO_CHANNEL": "Please specify a channel to post the dashboard.",
    "INVALID_CHANNEL": "Invalid channel specified.",
    "PERMISSION_ERROR": "Bot doesn't have permission to post in that channel.",
    "GENERAL_ERROR": "An error occurred while processing the dashboard."
}
