# src/cogs/user/commands/wrapper.py
from typing import Optional
import nextcord
from nextcord.ext import commands
from src.config.constants import TEST_GUILD_ID
from .get_started import get_started_command
from .view_profile import view_profile_command
from .update_profile import update_profile_command
from .schedule.command import ScheduleCommands
from .schedule.constants import (
    SCHEDULE_ADD_DESC,
    SCHEDULE_VIEW_DESC,
    SCHEDULE_CLEAR_DESC
)
import logging

logger = logging.getLogger(__name__)

class UserCommands(commands.Cog):
    """Wrapper for all user-facing commands.

    This cog serves as a central point for all user commands,
    organizing them into appropriate categories and managing their registration.

    Attributes:
        bot (commands.Bot): The bot instance
    """
    def __init__(self, bot):
        self.bot = bot
        self.schedule_commands = ScheduleCommands()
        logger.info("User commands initialized")

    @nextcord.slash_command(
        name="get-started",
        description="Set up your tennis profile and rating",
        guild_ids=[TEST_GUILD_ID]
    )
    async def get_started(self, interaction: nextcord.Interaction):
        """Set up your initial tennis profile."""
        await get_started_command(interaction)

    @nextcord.slash_command(
        name="view-profile",
        description="View your tennis profile details",
        guild_ids=[TEST_GUILD_ID]
    )
    async def view_profile(self, interaction: nextcord.Interaction):
        """View your complete tennis profile."""
        await view_profile_command(interaction)

    @nextcord.slash_command(
        name="update-profile",
        description="Update your tennis profile settings",
        guild_ids=[TEST_GUILD_ID]
    )
    async def update_profile(self, interaction: nextcord.Interaction):
        """Update your tennis profile settings."""
        await update_profile_command(interaction)

    @nextcord.slash_command(
        name="schedule",
        description="Manage your tennis schedule",
        guild_ids=[TEST_GUILD_ID]
    )
    async def schedule(self, interaction: nextcord.Interaction):
        """Schedule command group."""
        pass

    @schedule.subcommand(
        name="add",
        description=SCHEDULE_ADD_DESC
    )
    async def schedule_add(
        self,
        interaction: nextcord.Interaction,
        when: str = nextcord.SlashOption(
            name="when",
            description="When you want to play (e.g., 'today 4-6pm', 'wed/thur 3-5pm')",
            required=True
        )
    ):
        """Add your availability to the schedule."""
        await self.schedule_commands.add_schedule(interaction, when)

    @schedule.subcommand(
        name="view",
        description=SCHEDULE_VIEW_DESC
    )
    async def schedule_view(
        self,
        interaction: nextcord.Interaction,
        filter: str = nextcord.SlashOption(
            name="filter",
            description="When to view (e.g., 'today', 'this week')",
            required=False
        )
    ):
        """View schedules."""
        await self.schedule_commands.view_schedule(interaction, filter)

    @schedule.subcommand(
        name="clear",
        description=SCHEDULE_CLEAR_DESC
    )
    async def schedule_clear(
        self,
        interaction: nextcord.Interaction,
        period: str = nextcord.SlashOption(
            name="period",
            description="Period to clear (e.g., 'today', 'this week')",
            required=True
        )
    ):
        """Clear schedule for a period."""
        await self.schedule_commands.clear_schedule(interaction, period)

def setup(bot):
    bot.add_cog(UserCommands(bot))
    logger.info("User commands cog loaded")
