# src/cogs/user/welcome.py
"""
Welcome module for handling new member onboarding.

This module manages the initial welcome process for new members joining the server,
including role assignment, welcome messages, and initial setup instructions.
"""

import logging

import nextcord
from nextcord.ext import commands

from src.config.dynamodb_config import get_db
from src.utils.config_loader import ConfigLoader
from src.utils.role_manager import RoleManager

logger = logging.getLogger(__name__)


class Welcome(commands.Cog):
    """
    Handles new member welcome process.

    This cog manages the initial welcome for new members, including:
    - Assigning initial Court Visitor role
    - Sending welcome message
    - Directing new members to use the /get-started command

    Attributes:
        bot (commands.Bot): The Discord bot instance
        db: DynamoDB database instance for user data storage
        config_loader (ConfigLoader): Instance of configuration loader
        role_manager (RoleManager): Utility for managing member roles

    Example:
        To use this cog, add it to your bot:
        ```python
        bot.add_cog(Welcome(bot))
        ```
    """

    def __init__(self, bot: commands.Bot):
        """
        Initialize Welcome cog.

        Args:
            bot (commands.Bot): The Discord bot instance

        Raises:
            DatabaseConnectionError: If connection to DynamoDB fails
            ConfigurationError: If required configuration is missing
        """
        self.bot = bot
        self.db = get_db()
        self.config_loader = ConfigLoader()
        self.role_manager = RoleManager()
        logger.info("Welcome cog initialized")

    async def assign_visitor_role(self, member: nextcord.Member) -> bool:
        """
        Assign Court Visitor role to new member.

        Attempts to assign the initial visitor role to a new member using the
        role manager utility.

        Args:
            member (nextcord.Member): The Discord member to assign the role to

        Returns:
            bool: True if role assignment was successful, False otherwise

        Raises:
            RoleAssignmentError: If there's an error during role assignment
            ValueError: If the visitor role is not configured
        """
        try:
            success = await self.role_manager.add_role(member, 'visitor')
            if success:
                logger.info(f"Assigned visitor role to {member.name}")
            else:
                logger.error(f"Failed to assign visitor role to {member.name}")
            return success

        except Exception as e:
            logger.error(f"Error assigning visitor role: {e}", exc_info=True)
            return False

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member) -> None:
        """
        Handle new member joins.

        This event listener is triggered when a new member joins the server.
        It handles:
        1. Role assignment
        2. Welcome message creation and sending
        3. Initial setup instructions

        Args:
            member (nextcord.Member): The member who joined the server

        Note:
            This method uses configuration from guild_config.yaml for:
            - Welcome channel name
            - Welcome message content
            - Role names and permissions
        """
        try:
            # Assign Court Visitor role
            await self.assign_visitor_role(member)

            # Get welcome channel configuration
            welcome_channel_name = self.config_loader.get_channel_name('welcome')
            if not welcome_channel_name:
                logger.error("Welcome channel configuration not found")
                return

            welcome_channel = nextcord.utils.get(
                member.guild.channels,
                name=welcome_channel_name
            )

            if welcome_channel:
                # Get welcome message configuration
                welcome_config = self.config_loader.config.get('messages', {}).get('welcome', {})

                # Create welcome embed with configured or default messages
                welcome_embed = nextcord.Embed(
                    title=welcome_config.get('title', "Welcome! 🎾").format(
                        guild_name=member.guild.name,
                        member_name=member.name
                    ),
                    description=welcome_config.get('description', (
                        "Welcome to our tennis community!\n\n"
                        "Please use `/get-started` to set up your profile."
                    )),
                    color=nextcord.Color.green()
                )

                # Add member avatar if available
                if member.avatar:
                    welcome_embed.set_thumbnail(url=member.avatar.url)

                await welcome_channel.send(
                    content=member.mention,
                    embed=welcome_embed
                )

                logger.info(f"Sent welcome message for {member.name}")
            else:
                logger.error(f"Welcome channel '{welcome_channel_name}' not found")

        except Exception as e:
            logger.error(f"Error in on_member_join: {e}", exc_info=True)


def setup(bot: commands.Bot) -> None:
    """
    Set up the Welcome cog.

    Args:
        bot (commands.Bot): The Discord bot instance

    Example:
        ```python
        # In your bot's loading sequence:
        bot.load_extension('cogs.user.welcome')
        ```
    """
    bot.add_cog(Welcome(bot))
    logger.info("Welcome cog loaded")
