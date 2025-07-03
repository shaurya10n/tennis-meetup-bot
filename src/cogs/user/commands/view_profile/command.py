# src/cogs/user/commands/view_profile/command.py
"""Implementation of the /view-profile command."""

import logging
from datetime import datetime, timezone
from nextcord import Interaction, Embed, Color
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.config.dynamodb_config import get_db
from src.utils.responses import Responses
from src.cogs.user.commands.get_started.constants import (
    INTEREST_OPTIONS, SKILL_LEVEL_OPTIONS, GENDER_OPTIONS, PLAYER_GENDER_OPTIONS
)

logger = logging.getLogger(__name__)


async def view_profile_command(interaction: Interaction):
    """Display user's tennis profile.

    Args:
        interaction (Interaction): The Discord interaction object

    This command shows:
    - Current tennis level
    - Player's gender
    - Date of birth
    - Skill level preferences
    - Gender preference
    - Selected interests
    - Preferred locations
    - Profile creation date (if available)
    """
    try:
        player_dao = PlayerDAO(get_db())
        court_dao = CourtDAO(get_db())
        player = player_dao.get_player(interaction.guild.id, interaction.user.id)

        if not player:
            await Responses.send_warning(
                interaction,
                "Profile Not Found",
                "You haven't set up your profile yet. Use `/get-started` to create one.",
                ephemeral=True
            )
            return

        # Create profile embed
        embed = Embed(
            title=f"{player.username}'s Tennis Profile",
            color=Color.blue()
        )

        # Add NTRP rating field
        rating_text = f"NTRP Rating: {float(player.ntrp_rating)}"
        if not player.knows_ntrp:
            rating_text += " (Based on questionnaire)"
        
        # Add calibration status if still in calibration period
        if player.calibration_ends_at:
            # Parse ISO format string with UTC timezone
            calibration_end_date = datetime.fromisoformat(player.calibration_ends_at)
            now = datetime.now(timezone.utc)
            if calibration_end_date > now:
                days_left = (calibration_end_date - now).days
                rating_text += f"\n⚠️ Calibration period: {days_left} days remaining"
        
        if player.last_rating_update:
            # Parse ISO format string with UTC timezone
            last_update_date = datetime.fromisoformat(player.last_rating_update)
            rating_text += f"\nLast updated: {last_update_date.strftime('%Y-%m-%d')}"
        
        embed.add_field(
            name="Tennis Level",
            value=rating_text,
            inline=False
        )

        # Add player gender field
        if player.gender and player.gender in PLAYER_GENDER_OPTIONS:
            gender_text = f"{PLAYER_GENDER_OPTIONS[player.gender]['emoji']} {PLAYER_GENDER_OPTIONS[player.gender]['label']}"
        else:
            gender_text = "Not specified"
        embed.add_field(
            name="Gender",
            value=gender_text,
            inline=False
        )

        # Add date of birth field
        if player.dob:
            embed.add_field(
                name="Date of Birth",
                value=f"📅 {player.dob}",
                inline=False
            )

        # Add skill level preferences field
        skill_levels_text = "\n".join([
            f"{SKILL_LEVEL_OPTIONS[pref]['emoji']} {SKILL_LEVEL_OPTIONS[pref]['label']}"
            for pref in player.preferences.get("skill_levels", []) if pref in SKILL_LEVEL_OPTIONS
        ])
        embed.add_field(
            name="Skill Level Preferences",
            value=skill_levels_text or "No preferences selected",
            inline=False
        )

        # Add gender preference field
        gender_prefs = player.preferences.get("gender", [])
        if not gender_prefs:
            gender_text = "No preference set"
        elif isinstance(gender_prefs, list):
            # Handle list of gender preferences
            gender_text = "\n".join([
                f"{GENDER_OPTIONS[pref]['emoji']} {GENDER_OPTIONS[pref]['label']}"
                for pref in gender_prefs if pref in GENDER_OPTIONS
            ])
            if not gender_text:
                gender_text = "No preference set"
        else:
            # Handle single gender preference (string)
            if gender_prefs in GENDER_OPTIONS:
                gender_text = f"{GENDER_OPTIONS[gender_prefs]['emoji']} {GENDER_OPTIONS[gender_prefs]['label']}"
            else:
                gender_text = "No preference set"
        
        embed.add_field(
            name="Gender Preference",
            value=gender_text,
            inline=False
        )

        # Add location preferences field with court names
        locations_text = ""
        for court_id in player.preferences.get("locations", []):
            court = court_dao.get_court(court_id)
            if court:
                locations_text += f"📍 {court.name}\n"
            else:
                locations_text += f"📍 {court_id}\n"
        
        embed.add_field(
            name="Preferred Locations",
            value=locations_text or "No locations selected",
            inline=False
        )

        # Add interests field
        interests_text = "\n".join([
            f"{INTEREST_OPTIONS[i]['emoji']} {INTEREST_OPTIONS[i]['label']}"
            for i in player.interests if i in INTEREST_OPTIONS
        ])
        embed.add_field(
            name="Interests",
            value=interests_text or "No interests selected",
            inline=False
        )

        # Add timestamp if available
        if player.created_at:
            # Parse ISO format string
            created_date = datetime.fromisoformat(player.created_at)
            embed.set_footer(text=f"Profile created: {created_date.strftime('%Y-%m-%d')}")

        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"Displayed profile for user {interaction.user.id}")

    except Exception as e:
        logger.error(f"Error viewing profile: {e}", exc_info=True)
        await Responses.send_error(
            interaction,
            "Error Viewing Profile",
            "Failed to retrieve your profile information. Please try again."
        )
