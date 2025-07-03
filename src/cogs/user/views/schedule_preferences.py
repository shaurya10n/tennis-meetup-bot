# src/cogs/user/views/schedule_preferences.py
"""View for managing schedule preferences."""

import nextcord
from nextcord import Interaction, Embed, Color
import logging
from typing import Callable, List
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.models.dynamodb.schedule import Schedule
from src.database.models.dynamodb.player import Player
from src.config.dynamodb_config import get_db
from src.cogs.user.commands.get_started.constants import BUTTON_STYLES
from src.cogs.user.commands.get_started.constants import LOCATION_STEP, SKILL_LEVEL_STEP, GENDER_STEP
from .location_select import show_location_select
from .skill_level_select import show_skill_level_select
from .gender_select import show_gender_select

logger = logging.getLogger(__name__)

class SetPreferencesView(nextcord.ui.View):
    """Initial view asking if user wants to set preferences."""

    def __init__(
        self,
        schedule: Schedule,
        player: Player,
        callback: Callable[[Schedule], None]
    ):
        super().__init__()
        self.schedule = schedule
        self.player = player
        self.callback = callback
        self._add_buttons()

    def _add_buttons(self):
        """Add buttons for preference options."""
        # Add Keep button to use profile preferences (first and default)
        profile_button = nextcord.ui.Button(
            style=BUTTON_STYLES["success"],
            label="Keep",
            emoji="👤",
            custom_id="set_preferences_profile"
        )
        profile_button.callback = self._handle_profile
        self.add_item(profile_button)
        
        # Add Change button for custom preferences
        custom_button = nextcord.ui.Button(
            style=BUTTON_STYLES["unselected"],
            label="Change",
            emoji="✏️",
            custom_id="set_preferences_custom"
        )
        custom_button.callback = self._handle_custom
        self.add_item(custom_button)
        
        # Add Cancel button to cancel the interaction
        cancel_button = nextcord.ui.Button(
            style=nextcord.ButtonStyle.danger,
            label="Cancel",
            emoji="❌",
            custom_id="set_preferences_cancel"
        )
        cancel_button.callback = self._handle_cancel
        self.add_item(cancel_button)

    async def _handle_custom(self, interaction: Interaction):
        """Handle yes button click."""
        # Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        # Start location selection
        court_dao = CourtDAO(get_db())
        courts = court_dao.list_courts()
        locations = [(court.court_id, court.name) for court in courts]
        
        async def location_callback(i: Interaction, selected_locations: List[str]):
            # Store preferences in preference_overrides
            if not self.schedule.preference_overrides:
                self.schedule.preference_overrides = {}
                
            self.schedule.preference_overrides['location'] = selected_locations[0]  # Take first selected location
            
            # Create a modified step config based on SKILL_LEVEL_STEP
            schedule_skill_level_step = SKILL_LEVEL_STEP.copy()
            schedule_skill_level_step["title"] = "Schedule Skill Level"
            schedule_skill_level_step["description"] = "Select skill level preferences for this schedule:"
            
            # Move to skill level selection
            await show_skill_level_select(
                i,
                lambda si, levels: skill_level_callback(si, levels),
                schedule_skill_level_step
            )

        async def skill_level_callback(i: Interaction, selected_levels: List[str]):
            if not self.schedule.preference_overrides:
                self.schedule.preference_overrides = {}
                
            self.schedule.preference_overrides['skill_levels'] = selected_levels
            
            # Create a modified step config based on GENDER_STEP
            schedule_gender_step = GENDER_STEP.copy()
            schedule_gender_step["title"] = "Schedule Gender Preference"
            schedule_gender_step["description"] = "Select gender preference for this schedule:"
            
            # Move to gender preference selection
            await show_gender_select(
                i,
                lambda gi, gender: gender_callback(gi, gender),
                schedule_gender_step
            )

        async def gender_callback(i: Interaction, gender: str):
            if not self.schedule.preference_overrides:
                self.schedule.preference_overrides = {}
                
            self.schedule.preference_overrides['gender'] = gender
            
            # Update schedule in database
            schedule_dao = ScheduleDAO(get_db())
            try:
                updated_schedule = schedule_dao.update_schedule(
                    self.schedule.guild_id,
                    self.schedule.schedule_id,
                    preference_overrides=self.schedule.preference_overrides
                )
                
                await i.followup.send(
                    "Successfully updated schedule preferences!",
                    ephemeral=True
                )
                await self.callback(updated_schedule)
            except Exception as e:
                logger.error(f"Failed to update schedule preferences: {e}", exc_info=True)
                await i.followup.send(
                    "Failed to update schedule preferences. Please try again.",
                    ephemeral=True
                )

        # Create a modified step config based on LOCATION_STEP
        schedule_location_step = LOCATION_STEP.copy()
        schedule_location_step["title"] = "Schedule Location"
        schedule_location_step["description"] = "Select a location for this schedule:"
        
        await show_location_select(
            interaction,
            locations,
            location_callback,
            schedule_location_step
        )

    async def _handle_profile(self, interaction: Interaction):
        """Handle using profile preferences."""
        # Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Clear preference overrides to use profile preferences
        schedule_dao = ScheduleDAO(get_db())
        try:
            updated_schedule = schedule_dao.update_schedule(
                self.schedule.guild_id,
                self.schedule.schedule_id,
                preference_overrides={}
            )
            
            await interaction.followup.send(
                "Schedule will use your profile preferences.",
                ephemeral=True
            )
            await self.callback(updated_schedule)
        except Exception as e:
            logger.error(f"Failed to update schedule preferences: {e}", exc_info=True)
            await interaction.followup.send(
                "Failed to update schedule preferences. Please try again.",
                ephemeral=True
            )
            
    async def _handle_cancel(self, interaction: Interaction):
        """Handle cancellation of schedule addition."""
        # Disable buttons
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Inform user of cancellation
        await interaction.followup.send(
            "Schedule addition cancelled.",
            ephemeral=True
        )
        
        # Note: We don't call the callback or save anything to the database
        # since the user wants to cancel the interaction

async def show_schedule_preferences(
    interaction: Interaction,
    schedule: Schedule,
    callback: Callable[[Schedule], None]
) -> None:
    """Show the schedule preferences view.
    
    Args:
        interaction (Interaction): Discord interaction
        schedule (Schedule): Schedule to update preferences for
        callback (Callable): Function to call with updated schedule
    """
    try:
        guild_id = str(interaction.guild_id)
        discord_id = str(interaction.user.id)
        
        # Get player's profile
        player_dao = PlayerDAO(get_db())
        player = player_dao.get_player(guild_id, discord_id)  # Still use discord_id for player lookup
        
        if not player:
            await interaction.response.send_message(
                "Could not find your profile. Please complete profile setup first.",
                ephemeral=True
            )
            return

        # Format profile preferences
        preferences = player.preferences or {}
        locations = ", ".join(preferences.get('locations', []))
        skill_levels = ", ".join(level.capitalize() for level in preferences.get('skill_levels', []))
        gender = preferences.get('gender', 'none')
        gender_display = gender.capitalize() if gender != "none" else "No Preference"

        # Format date and time for display
        # Convert integer timestamps to datetime objects
        from datetime import datetime
        
        start_datetime = datetime.fromtimestamp(schedule.start_time, tz=schedule.timezone)
        end_datetime = datetime.fromtimestamp(schedule.end_time, tz=schedule.timezone)
        
        date_str = start_datetime.strftime("%A, %B %d")
        start_time_str = start_datetime.strftime("%I:%M %p")
        end_time_str = end_datetime.strftime("%I:%M %p")
        
        embed = Embed(
            title="Schedule Preferences",
            description=(
                f"Adding {date_str} from {start_time_str} to {end_time_str}, "
                f"would you like to keep your existing preferences for this schedule or change them?\n\n"
                "Your Profile Preferences:\n"
                f"📍 Location: {locations}\n"
                f"📊 Skill Level: {skill_levels}\n"
                f"👥 Gender: {gender_display}"
            ),
            color=Color.blue()
        )

        view = SetPreferencesView(schedule, player, callback)

        # Check if initial response has been made
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        logger.error(f"Error showing schedule preferences: {e}", exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "An error occurred. Please try again.",
                ephemeral=True
            )
