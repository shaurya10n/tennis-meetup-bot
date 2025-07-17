"""Dashboard command implementation."""

import logging
import nextcord
from datetime import datetime
from typing import Optional, Set, Dict, List
from zoneinfo import ZoneInfo

from src.config.dynamodb_config import get_db
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.utils.responses import Responses
from src.utils.config_loader import ConfigLoader
from .aggregator import ScheduleAggregator
from .constants import EMBEDS, SUCCESS, ERRORS
from .views.location_view import LocationAvailabilityView
from .views.playing_view import CurrentlyPlayingView

logger = logging.getLogger(__name__)

class DashboardCommands:
    """Handler for dashboard commands."""

    def __init__(self):
        """Initialize command handler."""
        db = get_db()
        self.schedule_dao = ScheduleDAO(db)
        self.player_dao = PlayerDAO(db)
        self.court_dao = CourtDAO(db)
        self.aggregator = ScheduleAggregator(self.schedule_dao, self.player_dao, self.court_dao)
        config_loader = ConfigLoader()
        self.timezone = config_loader.get_timezone()
        self.last_channel_id = None  # Track last channel where dashboard was posted

    async def view_dashboard(
        self,
        interaction: nextcord.Interaction,
        location: Optional[str] = None
    ):
        """View the availability dashboard.
        
        Args:
            interaction (nextcord.Interaction): Command interaction
            location (Optional[str]): Optional location filter
        """
        try:
            logger.info(
                f"Viewing dashboard - Admin: {interaction.user.name}, "
                f"Location filter: '{location}'"
            )
            
            # Defer response since this might take a while
            await interaction.response.defer(ephemeral=True)
            
            # Get availability data
            start_date = datetime.now(self.timezone).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            location_data = await self.aggregator.get_availability_by_location(
                start_date=start_date,
                location=location
            )
            
            if not location_data:
                await interaction.followup.send(
                    ERRORS["NO_SCHEDULES"],
                    ephemeral=True
                )
                return
                
            # Get all user IDs from the data
            user_ids = set()
            for loc_data in location_data.values():
                for date_data in loc_data.values():
                    for slot_data in date_data.values():
                        user_ids.update(slot_data)
            
            # Get user information
            user_dict = await self.aggregator.get_user_dict(user_ids)
            
            # Get locations
            locations = list(location_data.keys())
            
            # Create and send view
            view = LocationAvailabilityView(
                location_data=location_data,
                user_dict=user_dict,
                locations=locations
            )
            
            await interaction.followup.send(
                embed=await view.get_embed(),
                view=view,
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error viewing dashboard: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                EMBEDS["DASHBOARD_TITLE"],
                ERRORS["GENERAL_ERROR"],
                ephemeral=True
            )

    async def view_playing(self, interaction: nextcord.Interaction):
        """View currently playing users.
        
        Args:
            interaction (nextcord.Interaction): Command interaction
        """
        try:
            logger.info(f"Viewing currently playing - Admin: {interaction.user.name}")
            
            # Defer response since this might take a while
            await interaction.response.defer(ephemeral=True)
            
            # Get currently playing data
            playing_data = await self.aggregator.get_currently_playing()
            
            # Get all user IDs from the data
            user_ids = set()
            for players in playing_data.values():
                for user_id, _, _ in players:
                    user_ids.add(user_id)
            
            # Get user information
            user_dict = await self.aggregator.get_user_dict(user_ids)
            
            # Create and send view
            view = CurrentlyPlayingView(
                playing_data=playing_data,
                user_dict=user_dict
            )
            
            await interaction.followup.send(
                embed=await view.get_embed(),
                view=view,
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error viewing currently playing: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                EMBEDS["PLAYING_TITLE"],
                ERRORS["GENERAL_ERROR"],
                ephemeral=True
            )

    async def post_dashboard(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel
    ):
        """Post the dashboard to a channel.
        
        Args:
            interaction (nextcord.Interaction): Command interaction
            channel (nextcord.TextChannel): Channel to post to
        """
        try:
            logger.info(
                f"Posting dashboard - Admin: {interaction.user.name}, "
                f"Channel: {channel.name}"
            )
            
            # Defer response
            await interaction.response.defer(ephemeral=True)
            
            # Check permissions
            if not channel.permissions_for(interaction.guild.me).send_messages:
                await interaction.followup.send(
                    ERRORS["PERMISSION_ERROR"],
                    ephemeral=True
                )
                return
                
            # Get availability data
            start_date = datetime.now(self.timezone).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            location_data = await self.aggregator.get_availability_by_location(
                start_date=start_date
            )
            
            if not location_data:
                await interaction.followup.send(
                    ERRORS["NO_SCHEDULES"],
                    ephemeral=True
                )
                return
                
            # Get all user IDs from the data
            user_ids = set()
            for loc_data in location_data.values():
                for date_data in loc_data.values():
                    for slot_data in date_data.values():
                        user_ids.update(slot_data)
            
            # Get user information
            user_dict = await self.aggregator.get_user_dict(user_ids)
            
            # Get locations
            locations = list(location_data.keys())
            
            # Create view
            view = LocationAvailabilityView(
                location_data=location_data,
                user_dict=user_dict,
                locations=locations
            )
            
            # Post to channel
            await channel.send(
                embed=await view.get_embed(),
                view=view
            )
            
            # Store channel ID for refresh command
            self.last_channel_id = channel.id
            
            # Send success message
            await interaction.followup.send(
                SUCCESS["DASHBOARD_POSTED"].format(channel=channel.mention),
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error posting dashboard: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                EMBEDS["DASHBOARD_TITLE"],
                ERRORS["GENERAL_ERROR"],
                ephemeral=True
            )

    async def refresh_dashboard(self, interaction: nextcord.Interaction):
        """Refresh the dashboard in the last channel it was posted to.
        
        Args:
            interaction (nextcord.Interaction): Command interaction
        """
        try:
            logger.info(f"Refreshing dashboard - Admin: {interaction.user.name}")
            
            # Defer response
            await interaction.response.defer(ephemeral=True)
            
            # Check if we have a last channel
            if not self.last_channel_id:
                await interaction.followup.send(
                    ERRORS["NO_CHANNEL"],
                    ephemeral=True
                )
                return
                
            # Get channel
            channel = interaction.guild.get_channel(self.last_channel_id)
            if not channel:
                await interaction.followup.send(
                    ERRORS["INVALID_CHANNEL"],
                    ephemeral=True
                )
                return
                
            # Check permissions
            if not channel.permissions_for(interaction.guild.me).send_messages:
                await interaction.followup.send(
                    ERRORS["PERMISSION_ERROR"],
                    ephemeral=True
                )
                return
                
            # Get availability data
            start_date = datetime.now(self.timezone).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            location_data = await self.aggregator.get_availability_by_location(
                start_date=start_date
            )
            
            if not location_data:
                await interaction.followup.send(
                    ERRORS["NO_SCHEDULES"],
                    ephemeral=True
                )
                return
                
            # Get all user IDs from the data
            user_ids = set()
            for loc_data in location_data.values():
                for date_data in loc_data.values():
                    for slot_data in date_data.values():
                        user_ids.update(slot_data)
            
            # Get user information
            user_dict = await self.aggregator.get_user_dict(user_ids)
            
            # Get locations
            locations = list(location_data.keys())
            
            # Create view
            view = LocationAvailabilityView(
                location_data=location_data,
                user_dict=user_dict,
                locations=locations
            )
            
            # Post to channel
            await channel.send(
                embed=await view.get_embed(),
                view=view
            )
            
            # Send success message
            await interaction.followup.send(
                SUCCESS["DASHBOARD_REFRESHED"],
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error refreshing dashboard: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                EMBEDS["DASHBOARD_TITLE"],
                ERRORS["GENERAL_ERROR"],
                ephemeral=True
            )
