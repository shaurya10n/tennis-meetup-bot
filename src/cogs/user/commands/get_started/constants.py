# src/cogs/user/commands/get_started/constants.py
"""Constants for the get-started command UI and flow."""
import nextcord

# NTRP Step
NTRP_STEP = {
    "title": "Tennis Profile Setup (1/7)",
    "header": {
        "emoji": "🎾",
        "title": "NTRP RATING",
        "separator": "———————————————"
    },
    "description": (
        "The National Tennis Rating Program (NTRP) helps match players of similar skill levels.\n\n"
        "Do you know your NTRP rating?"
    ),
    "explanation": (
        "• If you've played USTA leagues or tournaments, you likely have an NTRP rating.\n"
        "• If you're new to tennis or unsure, we'll ask a few questions to estimate your level.\n"
        "• Your rating can be adjusted later during a 2-week calibration period."
    )
}

NTRP_INFO = {
    "description": """
The National Tennis Rating Program (NTRP) is the official system for determining 
the levels of competition for tennis players.

The ratings range from 1.0 to 7.0:
• 2.0-2.5: Beginner to Advanced Beginner
• 3.0-3.5: Intermediate
• 4.0-4.5: Advanced Intermediate
• 5.0+: Advanced/Tournament Level
    """,
    "help_link": "https://www.usta.com/en/home/play/adult-tennis/programs/national/about-ntrp-ratings.html"
}

NTRP_RANGES = {
    "beginner": {
        "value": 1.5,
        "range": "1.0-2.0",
        "label": "Beginner",
        "emoji": "🌱",
        "description": "New to tennis, learning basic strokes and rules"
    },
    "adv_beginner": {
        "value": 2.5,
        "range": "2.0-3.0",
        "label": "Advanced Beginner",
        "emoji": "🎾",
        "description": "Basic strokes established, developing consistency and court awareness"
    },
    "intermediate": {
        "value": 3.5,
        "range": "3.0-4.0",
        "label": "Intermediate",
        "emoji": "🎯",
        "description": "Consistent rallies, dependable strokes, basic strategy and spin control"
    },
    "adv_intermediate": {
        "value": 4.5,
        "range": "4.0-5.0",
        "label": "Advanced Intermediate",
        "emoji": "⭐",
        "description": "Strong all-court game, power and spin shots, tactical play"
    },
    "advanced": {
        "value": 5.5,
        "range": "5.0+",
        "label": "Advanced",
        "emoji": "🏆",
        "description": "Tournament level, advanced skills, tactics and competitive experience"
    }
}

NTRP_CONFIG = {
    "min_rating": 1.5,
    "max_rating": 5.5,
    "round_to": 0.5,
    "calibration_period_days": 14,
    "update_cooldown_days": 30
}

NTRP_QUESTIONS = {
    "experience": {
        "text": "How long have you been playing tennis?",
        "weight": 1.0,
        "answers": [
            {"value": 1.5, "text": "Just started / Less than 3 months"},
            {"value": 2.5, "text": "3 months to 1 year"},
            {"value": 3.5, "text": "1-3 years"},
            {"value": 4.5, "text": "3-5 years"},
            {"value": 5.5, "text": "5+ years with competitive experience"}
        ]
    },
    "serve": {
        "text": "Which best describes your serve?",
        "weight": 1.5,
        "answers": [
            {"value": 1.5, "text": "Learning the basic serve motion"},
            {"value": 2.5, "text": "Can serve but working on consistency"},
            {"value": 3.5, "text": "Consistent serves with direction control"},
            {"value": 4.5, "text": "Power serves with spin variations"},
            {"value": 5.5, "text": "Weapon serve with advanced placement"}
        ]
    },
    "rally": {
        "text": "How would you describe your rallying ability?",
        "weight": 2.0,  # Highest weight as it's most indicative of level
        "answers": [
            {"value": 1.5, "text": "Learning to make contact consistently"},
            {"value": 2.5, "text": "Can maintain basic rallies"},
            {"value": 3.5, "text": "Consistent rallies with direction control"},
            {"value": 4.5, "text": "Strong rallies with spin and depth"},
            {"value": 5.5, "text": "Advanced shot selection and court control"}
        ]
    },
    "match": {
        "text": "What's your match experience level?",
        "weight": 1.5,  # Increased weight as it indicates overall level
        "answers": [
            {"value": 1.5, "text": "No match experience yet"},
            {"value": 2.5, "text": "Casual matches with friends"},
            {"value": 3.5, "text": "Regular social matches"},
            {"value": 4.5, "text": "League matches or local tournaments"},
            {"value": 5.5, "text": "Regular tournament competition"}
        ]
    },
    "strategy": {  # Changed from volley to strategy
        "text": "How would you describe your game strategy?",
        "weight": 1.5,  # Increased weight as it indicates overall development
        "answers": [
            {"value": 1.5, "text": "Learning basic positioning"},
            {"value": 2.5, "text": "Understanding basic court positioning"},
            {"value": 3.5, "text": "Can execute game plans"},
            {"value": 4.5, "text": "Adapts tactics during matches"},
            {"value": 5.5, "text": "Advanced tactics and match management"}
        ]
    }
}

# Player Gender Step
PLAYER_GENDER_STEP = {
    "title": "Tennis Profile Setup (2/7)",
    "header": {
        "emoji": "👤",
        "title": "YOUR GENDER",
        "separator": "———————————————"
    },
    "description": "Please select your gender:"
}

PLAYER_GENDER_OPTIONS = {
    "male": {
        "label": "Male",
        "emoji": "👨",
        "description": "Identify as male",
        "value": "male"
    },
    "female": {
        "label": "Female",
        "emoji": "👩",
        "description": "Identify as female",
        "value": "female"
    },
    "non_binary": {
        "label": "Non-Binary",
        "emoji": "🏳️‍🌈",
        "description": "Identify as non-binary",
        "value": "non_binary"
    },
    "prefer_not_to_say": {
        "label": "Prefer Not to Say",
        "emoji": "🔒",
        "description": "Prefer not to disclose",
        "value": "prefer_not_to_say"
    }
}

# Date of Birth Step
DOB_STEP = {
    "title": "Tennis Profile Setup (3/7)",
    "header": {
        "emoji": "📅",
        "title": "DATE OF BIRTH",
        "separator": "———————————————"
    },
    "description": "Please enter your date of birth (MM/DD/YYYY):"
}

# Skill Level Preference Step
SKILL_LEVEL_STEP = {
    "title": "Tennis Profile Setup (4/7)",
    "header": {
        "emoji": "📊",
        "title": "SKILL LEVEL PREFERENCES",
        "separator": "———————————————"
    },
    "description": "Select your preferred opponent skill levels (can select multiple):"
}

SKILL_LEVEL_OPTIONS = {
    "similar": {
        "label": "Similar Level (±0.5 NTRP)",
        "emoji": "⚖️",
        "description": "Players at your skill level",
        "value": "similar"
    },
    "above": {
        "label": "Level Above (+1.0 NTRP)",
        "emoji": "📈",
        "description": "Players with higher skill level",
        "value": "above"
    },
    "below": {
        "label": "Level Below (-1.0 NTRP)",
        "emoji": "📉",
        "description": "Help others improve their game",
        "value": "below"
    },
    "any": {
        "label": "Any Level",
        "emoji": "🔄",
        "description": "Open to all skill levels",
        "value": "any"
    }
}

# Gender Preference Step
GENDER_STEP = {
    "title": "Tennis Profile Setup (5/7)",
    "header": {
        "emoji": "👥",
        "title": "GENDER PREFERENCE",
        "separator": "———————————————"
    },
    "description": "Do you have a gender preference for your tennis matches (can select multiple)?"
}

GENDER_OPTIONS = {
    "none": {
        "label": "No Preference",
        "emoji": "🤝",
        "description": "Open to playing with anyone",
        "value": "none"
    },
    "men": {
        "label": "Men",
        "emoji": "👨",
        "description": "Prefer to play with men",
        "value": "men"
    },
    "women": {
        "label": "Women",
        "emoji": "👩",
        "description": "Prefer to play with women",
        "value": "women"
    },
    "non_binary": {
        "label": "Non-Binary",
        "emoji": "🏳️‍🌈",
        "description": "Prefer to play with non-binary individuals",
        "value": "non_binary"
    }
}

# Interest Step
INTEREST_STEP = {
    "title": "Tennis Profile Setup (6/7)",
    "header": {
        "emoji": "🎯",
        "title": "INTERESTS",
        "separator": "———————————————"
    },
    "description": "What are you interested in? (can select multiple)"
}

INTEREST_OPTIONS = {
    "regular_hits": {
        "label": "Regular Hits",
        "emoji": "🎾",
        "description": "Practice sessions and rallies"
    },
    "matches": {
        "label": "Matches",
        "emoji": "🏆",
        "description": "Competitive matches"
    },
    "coaching": {
        "label": "Coaching",
        "emoji": "👨‍🏫",
        "description": "Learning and improvement"
    },
    "social": {
        "label": "Social Hangouts",
        "emoji": "🤝",
        "description": "Tennis and socializing"
    }
}



# Location Step
LOCATION_STEP = {
    "title": "Tennis Profile Setup (7/7)",
    "header": {
        "emoji": "📍",
        "title": "LOCATIONS",
        "separator": "———————————————"
    },
    "description": "Choose your preferred court locations (can select multiple):"
}

# Button styles
BUTTON_STYLES = {
    "selected": nextcord.ButtonStyle.primary,
    "unselected": nextcord.ButtonStyle.secondary,
    "success": nextcord.ButtonStyle.success,
    "info": nextcord.ButtonStyle.secondary
}
