# src/cogs/user/commands/update_profile/constants.py
"""Constants for the update-profile command."""
import nextcord

UPDATE_OPTIONS = {
    "ntrp": {
        "label": "Update NTRP Rating",
        "emoji": "🎾",
        "description": "Change your NTRP rating"
    },
    "skill_level": {
        "label": "Update Skill Level Preferences",
        "emoji": "📊",
        "description": "Change your preferred opponent skill levels"
    },
    "gender": {
        "label": "Update Gender Preference",
        "emoji": "👥",
        "description": "Change your gender preference for matches"
    },
    "locations": {
        "label": "Update Locations",
        "emoji": "📍",
        "description": "Change your preferred court locations"
    },
    "interests": {
        "label": "Update Interests",
        "emoji": "🎯",
        "description": "Modify your tennis interests"
    }
}

UPDATE_MESSAGES = {
    "select_option": "What would you like to update?",
    "current_ntrp": "Your current NTRP rating: {}",
    "current_skill_levels": "Your current skill level preferences:\n{}",
    "current_gender": "Your current gender preference: {}",
    "current_locations": "Your current preferred locations:\n{}",
    "current_interests": "Your current interests:\n{}",
    "success": "Profile updated successfully!",
    "no_changes": "No changes were made to your profile.",
    "rating_update_warning": "Note: Your rating can be adjusted during the 2-week calibration period."
}

# Button styles
BUTTON_STYLES = {
    "selected": nextcord.ButtonStyle.primary,
    "unselected": nextcord.ButtonStyle.secondary,
    "success": nextcord.ButtonStyle.success,
    "info": nextcord.ButtonStyle.secondary
}
