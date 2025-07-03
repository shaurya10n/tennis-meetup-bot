# src/cogs/admin/admin.py
import logging
import traceback

import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from src.config.constants import TEST_GUILD_ID
from src.utils.config_loader import ConfigLoader
from src.utils.responses import Responses
from .setup.channels import ChannelSetup
from .setup.roles import RoleSetup
from .dashboard.command import DashboardCommands

logger = logging.getLogger(__name__)

class Admin(commands.Cog):
    """Administrative commands for server setup and management.

    This cog handles all administrative commands, primarily focusing on
    server setup operations like roles and channels configuration.
    Only the server owner can use these commands, and they must be used
    in the bot-admin channel.

    Attributes:
        bot (commands.Bot): The bot instance
        role_setup (RoleSetup): Handler for role setup operations
        channel_setup (ChannelSetup): Handler for channel setup operations
    """

    def __init__(self, bot):
        self.bot = bot
        self.role_setup = RoleSetup(bot)
        self.channel_setup = ChannelSetup(bot)
        self.dashboard_commands = DashboardCommands()

    async def validate_command_usage(self, interaction: Interaction) -> bool:
        """Validate if the command can be used."""
        try:
            # Get admin channel name using the ConfigLoader method
            admin_channel_name = ConfigLoader().get_channel_name('admin')
            logger.debug(f"Admin channel name: {admin_channel_name}")

            if not admin_channel_name:
                logger.error("Admin channel name not found in config")
                await Responses.send_error(
                    interaction,
                    "Configuration Error",
                    "Admin channel configuration is missing.",
                    ephemeral=True
                )
                return False

            # Check if user is server owner
            if interaction.user.id != interaction.guild.owner_id:
                await Responses.send_error(
                    interaction,
                    "Permission Denied",
                    "Only the server owner can use this command.",
                    ephemeral=True
                )
                logger.warning(f"Non-owner {interaction.user} attempted to use admin command")
                return False

            # Check if command is used in bot-admin channel
            if interaction.channel.name != admin_channel_name:
                await Responses.send_error(
                    interaction,
                    "Wrong Channel",
                    f"Please use this command in the {admin_channel_name} channel.",
                    ephemeral=True
                )
                logger.warning(f"Admin command used in wrong channel: {interaction.channel.name}")
                return False

            return True

        except Exception as e:
            logger.error("Error in command validation:", exc_info=True)
            await Responses.send_error(
                interaction,
                "Validation Error",
                "An error occurred while validating command usage.",
                ephemeral=True
            )
            return False

    @nextcord.slash_command(
        name="admin",
        description="Administrative commands",
        default_member_permissions=(nextcord.Permissions(administrator=True)),
        guild_ids=[TEST_GUILD_ID]
    )
    async def admin(self, interaction: Interaction):
        """Base admin command group."""
        pass

    @admin.subcommand(
        name="setup",
        description="Set up server configuration"
    )
    async def setup(self, interaction: Interaction):
        """Base setup command group."""
        pass

    @setup.subcommand(
        name="roles",
        description="Set up server roles"
    )
    async def setup_roles(self, interaction: Interaction):
        """Set up server roles configuration.

        Only the server owner can use this command, and it must be used
        in the bot-admin channel.

        Args:
            interaction (Interaction): The slash command interaction
        """
        try:
            # Validate command usage
            if not await self.validate_command_usage(interaction):
                return

            logger.info(f"Role setup initiated by server owner in {interaction.guild.name}")
            await self.role_setup.setup_roles(interaction)

        except Exception as e:
            logger.error(f"Error in setup_roles: {e}")
            await Responses.send_error(
                interaction,
                "Role Setup Failed",
                str(e)
            )

    @setup.subcommand(
        name="channels",
        description="Set up server channels"
    )
    async def setup_channels(self, interaction: Interaction):
        """Set up server channels configuration.

        Only the server owner can use this command, and it must be used
        in the bot-admin channel.

        Args:
            interaction (Interaction): The slash command interaction
        """
        try:
            # Validate command usage
            if not await self.validate_command_usage(interaction):
                return

            logger.info(f"Channel setup initiated by server owner in {interaction.guild.name}")
            await self.channel_setup.setup_channels(interaction)

        except Exception as e:
            logger.error(f"Error in setup_channels: {e}")
            await Responses.send_error(
                interaction,
                "Channel Setup Failed",
                str(e)
            )

    @admin.subcommand(
        name="dashboard",
        description="Availability dashboard commands"
    )
    async def dashboard(self, interaction: Interaction):
        """Base dashboard command group."""
        pass
        
    @dashboard.subcommand(
        name="view",
        description="View the availability dashboard"
    )
    async def view_dashboard(
        self,
        interaction: Interaction,
        location: str = nextcord.SlashOption(
            description="Filter by location",
            required=False
        )
    ):
        """View the availability dashboard.
        
        Args:
            interaction (Interaction): The slash command interaction
            location (str, optional): Location filter
        """
        try:
            # Validate command usage
            if not await self.validate_command_usage(interaction):
                return
                
            logger.info(f"Dashboard view initiated by admin in {interaction.guild.name}")
            await self.dashboard_commands.view_dashboard(interaction, location)
            
        except Exception as e:
            logger.error(f"Error in view_dashboard: {e}")
            await Responses.send_error(
                interaction,
                "Dashboard View Failed",
                str(e)
            )
            
    @dashboard.subcommand(
        name="playing",
        description="View currently playing users"
    )
    async def view_playing(self, interaction: Interaction):
        """View currently playing users.
        
        Args:
            interaction (Interaction): The slash command interaction
        """
        try:
            # Validate command usage
            if not await self.validate_command_usage(interaction):
                return
                
            logger.info(f"Currently playing view initiated by admin in {interaction.guild.name}")
            await self.dashboard_commands.view_playing(interaction)
            
        except Exception as e:
            logger.error(f"Error in view_playing: {e}")
            await Responses.send_error(
                interaction,
                "Currently Playing View Failed",
                str(e)
            )
            
    @dashboard.subcommand(
        name="post",
        description="Post the dashboard to a channel"
    )
    async def post_dashboard(
        self,
        interaction: Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            description="Channel to post the dashboard to",
            required=True
        )
    ):
        """Post the dashboard to a channel.
        
        Args:
            interaction (Interaction): The slash command interaction
            channel (TextChannel): Channel to post to
        """
        try:
            # Validate command usage
            if not await self.validate_command_usage(interaction):
                return
                
            logger.info(f"Dashboard post initiated by admin in {interaction.guild.name}")
            await self.dashboard_commands.post_dashboard(interaction, channel)
            
        except Exception as e:
            logger.error(f"Error in post_dashboard: {e}")
            await Responses.send_error(
                interaction,
                "Dashboard Post Failed",
                str(e)
            )
            
    @dashboard.subcommand(
        name="refresh",
        description="Refresh the dashboard in the last channel it was posted to"
    )
    async def refresh_dashboard(self, interaction: Interaction):
        """Refresh the dashboard in the last channel it was posted to.
        
        Args:
            interaction (Interaction): The slash command interaction
        """
        try:
            # Validate command usage
            if not await self.validate_command_usage(interaction):
                return
                
            logger.info(f"Dashboard refresh initiated by admin in {interaction.guild.name}")
            await self.dashboard_commands.refresh_dashboard(interaction)
            
        except Exception as e:
            logger.error(f"Error in refresh_dashboard: {e}")
            await Responses.send_error(
                interaction,
                "Dashboard Refresh Failed",
                str(e)
            )


def setup(bot):
    bot.add_cog(Admin(bot))
    logger.info("Admin cog loaded")
