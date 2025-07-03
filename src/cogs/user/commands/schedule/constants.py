"""Constants for schedule commands."""

# Command descriptions
SCHEDULE_ADD_DESC = "Add your availability to play tennis"
SCHEDULE_VIEW_DESC = "View tennis schedules"
SCHEDULE_CLEAR_DESC = "Clear your schedules for a period"

# Error messages
ERRORS = {
    "INVALID_TIME_FORMAT": "❌ Could not understand time format. Examples:\n- today 4-6pm\n- next monday 3-5pm\n- tomorrow afternoon",
    "PAST_TIME": "❌ Cannot schedule in the past",
    "INVALID_DURATION": "❌ Schedule duration must be between 30 minutes and 4 hours",
    "OVERLAPPING": "❌ This schedule overlaps with your existing schedule",
    "NOT_FOUND": "❌ No matching schedule found",
    "SAVE_FAILED": "❌ Failed to save schedule. Please try again",
    "DELETE_FAILED": "❌ Failed to delete schedule. Please try again",
    "INVALID_FILTER": "❌ Invalid filter. Examples:\n- today\n- this week\n- next week",
    "INCOMPLETE_PROFILE": "❌ Please complete your profile before using schedule commands.\n\nMissing information:\n{missing_fields}\n\nUse /get-started to complete your profile.",
    "GENERAL_ERROR": "❌ An error occurred. Please try again"
}

# Success messages
SUCCESS = {
    "SCHEDULE_ADDED": "✅ Schedule added for {date} from {start_time} to {end_time}{recurrence_str}",
    "SCHEDULES_CLEARED": "✅ Schedules cleared successfully!"
}

# Embed titles
EMBEDS = {
    "ADD_SCHEDULE": "📅 Add Schedule",
    "VIEW_SCHEDULE": "📅 View Schedule",
    "CLEAR_SCHEDULE": "🧹 Clear Schedule",
    "CONFIRM_ACTION": "❓ Confirm Action"
}

# Time periods for schedule viewing/clearing
TIME_PERIODS = {
    "TODAY": "today",
    "TOMORROW": "tomorrow",
    "THIS_WEEK": "this week",
    "NEXT_WEEK": "next week"
}

# Button labels
BUTTONS = {
    "CONFIRM": "✅ Confirm",
    "CANCEL": "❌ Cancel",
    "PREVIOUS": "◀️ Previous",
    "NEXT": "▶️ Next"
}

# Schedule display format
SCHEDULE_FORMAT = "{time}"
TIME_FORMAT = "%I:%M %p"  # 12-hour format with AM/PM (e.g., 05:00 PM)
DATE_FORMAT = "%A, %B %d"  # e.g., Monday, January 1

# Confirmation messages
CONFIRM_MESSAGES = {
    "CLEAR_SCHEDULE": "Are you sure you want to clear your schedule for {period}?"
}

# Help messages
HELP = {
    "TIME_FORMAT": """
Time Format Examples:
- today 4-6pm
- next week tuesday 3-5pm
- tomorrow afternoon
- every monday 4-6pm
- next monday 3-5pm
""",
    "FILTER_FORMAT": """
Filter Format Examples:
- today
- tomorrow
- this week
- next week
"""
}

# Recurrence types
RECURRENCE_TYPES = {
    "DAILY": "daily",
    "WEEKLY": "weekly",
    "MONTHLY": "monthly"
}
