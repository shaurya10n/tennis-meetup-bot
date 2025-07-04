"""Views for displaying schedules."""

import nextcord
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Tuple
from src.database.models.dynamodb.schedule import Schedule
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.config.dynamodb_config import get_db
from ..constants import BUTTONS, DATE_FORMAT, TIME_FORMAT

logger = logging.getLogger(__name__)

class ScheduleListView(nextcord.ui.View):
    """View for displaying a list of schedules."""

    def __init__(
        self,
        schedules: List[Schedule],
        user_dict: Dict[str, str],
        page_size: int = 5
    ):
        """Initialize view with schedules.
        
        Args:
            schedules (List[Schedule]): List of schedules to display
            user_dict (Dict[str, str]): Mapping of user IDs to display names
            page_size (int, optional): Number of schedules per page
        """
        super().__init__(timeout=180)  # 3 minute timeout
        self.schedules = sorted(schedules, key=lambda s: s.start_time)
        self.user_dict = user_dict
        self.page_size = page_size
        self.current_page = 0
        self.total_pages = (len(schedules) - 1) // page_size + 1

        # Update button states
        self._update_buttons()

    def _update_buttons(self):
        """Update button states based on current page."""
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1

    async def get_current_page_embed(self) -> nextcord.Embed:
        """Get embed for current page of schedules."""
        embed = nextcord.Embed(
            title="📅 Tennis Schedules",
            color=0x00ff00
        )

        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.schedules))
        page_schedules = self.schedules[start_idx:end_idx]

        if not page_schedules:
            embed.description = "No schedules found."
            return embed

        # Group schedules by date
        date_groups = {}
        for schedule in page_schedules:
            # Convert integer timestamp to datetime
            start_datetime = datetime.fromtimestamp(schedule.start_time, tz=schedule.timezone)
            date = start_datetime.strftime(DATE_FORMAT)
            
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(schedule)

        # Add fields for each date
        for date, schedules in date_groups.items():
            schedule_lines = []
            for schedule in schedules:
                user_name = self.user_dict.get(schedule.user_id, f"User {schedule.user_id}")
                
                # Format times in schedule's timezone
                start_datetime = datetime.fromtimestamp(schedule.start_time, tz=schedule.timezone)
                end_datetime = datetime.fromtimestamp(schedule.end_time, tz=schedule.timezone)
                
                time_str = (
                    f"{start_datetime.strftime(TIME_FORMAT)} - "
                    f"{end_datetime.strftime(TIME_FORMAT)}"
                )
                
                # Get schedule info parts
                info_parts = []
                
                # Add status info if not open
                if schedule.status != "open":
                    status_emoji = "🔒" if schedule.status == "closed" else "❌"
                    info_parts.append(f"{status_emoji} {schedule.status.capitalize()}")
                
                # Add recurrence info
                if schedule.recurrence:
                    recurrence_type = schedule.recurrence.get('type')
                    if recurrence_type == 'daily':
                        info_parts.append("🔄 Daily")
                    elif recurrence_type == 'weekly':
                        days = schedule.recurrence.get('days', [])
                        if days:
                            day_names = [day.capitalize() for day in days]
                            info_parts.append(f"🔄 Weekly on {', '.join(day_names)}")
                        else:
                            info_parts.append("🔄 Weekly")
                    elif recurrence_type == 'monthly':
                        info_parts.append("🔄 Monthly")
                
                # Add recurring instance info
                if schedule.is_recurring_instance():
                    info_parts.append("🔄 Part of series")

                # Get preferences info
                prefs = await self._get_preferences(schedule)
                if prefs:
                    location, skill_levels, gender = prefs
                    if location:
                        info_parts.append(f"📍 {location}")
                    if skill_levels:
                        info_parts.append(f"📊 {', '.join(skill_levels)}")
                    if gender and gender != "none":
                        info_parts.append(f"👥 {', '.join(g.capitalize() for g in gender)} Only")

                # Format the line
                info_str = f" ({' | '.join(info_parts)})" if info_parts else ""
                schedule_lines.append(f"• {user_name}: {time_str}{info_str}")

            embed.add_field(
                name=date,
                value="\n".join(schedule_lines),
                inline=False
            )

        # Add page info
        embed.set_footer(text=f"Page {self.current_page + 1} of {self.total_pages}")
        return embed

    async def _get_preferences(self, schedule: Schedule) -> Optional[Tuple[str, List[str], str]]:
        """Get preferences for a schedule, either from profile or custom.
        
        Args:
            schedule (Schedule): The schedule to get preferences for
            
        Returns:
            Optional[Tuple[str, List[str], str]]: (location, skill_levels, gender) or None if error
        """
        try:
            # Check if schedule has preference overrides
            if schedule.preference_overrides:
                location = schedule.preference_overrides.get('location')
                skill_levels = schedule.preference_overrides.get('skill_levels', [])
                gender = schedule.preference_overrides.get('gender')
                
                if any([location, skill_levels, gender]):
                    return (
                        location,
                        [level.capitalize() for level in skill_levels] if skill_levels else [],
                        gender
                    )
            
            # If no overrides or they're empty, get from player profile
            player_dao = PlayerDAO(get_db())
            player = player_dao.get_player(schedule.guild_id, schedule.user_id)
            if player and player.preferences:
                return (
                    player.preferences.get('locations', [None])[0],
                    [level.capitalize() for level in player.preferences.get('skill_levels', [])],
                    player.preferences.get('gender')
                )
            
            # Default to schedule location if available
            if schedule.location:
                return (schedule.location, [], None)
                
            return None
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return None

    @nextcord.ui.button(
        label=BUTTONS["PREVIOUS"],
        style=nextcord.ButtonStyle.gray,
        disabled=True
    )
    async def previous_button(
        self,
        button: nextcord.ui.Button,
        interaction: nextcord.Interaction
    ):
        """Handle previous page button click."""
        self.current_page = max(0, self.current_page - 1)
        self._update_buttons()
        await interaction.response.edit_message(
            embed=await self.get_current_page_embed(),
            view=self
        )

    @nextcord.ui.button(
        label=BUTTONS["NEXT"],
        style=nextcord.ButtonStyle.gray,
        disabled=True
    )
    async def next_button(
        self,
        button: nextcord.ui.Button,
        interaction: nextcord.Interaction
    ):
        """Handle next page button click."""
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self._update_buttons()
        await interaction.response.edit_message(
            embed=await self.get_current_page_embed(),
            view=self
        )

class ConfirmView(nextcord.ui.View):
    """View for confirming an action."""

    def __init__(self, callback: Callable):
        """Initialize view with callback.
        
        Args:
            callback (Callable): Function to call when confirmed
        """
        super().__init__(timeout=60)  # 1 minute timeout
        self.callback = callback

    @nextcord.ui.button(
        label=BUTTONS["CONFIRM"],
        style=nextcord.ButtonStyle.green
    )
    async def confirm_button(
        self,
        button: nextcord.ui.Button,
        interaction: nextcord.Interaction
    ):
        """Handle confirm button click."""
        await self.callback(interaction)

    @nextcord.ui.button(
        label=BUTTONS["CANCEL"],
        style=nextcord.ButtonStyle.red
    )
    async def cancel_button(
        self,
        button: nextcord.ui.Button,
        interaction: nextcord.Interaction
    ):
        """Handle cancel button click."""
        await interaction.response.edit_message(
            content="Action cancelled.",
            view=None
        )
