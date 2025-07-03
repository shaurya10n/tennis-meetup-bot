"""
Tennis Meetup Discord Bot - Main Module

This is the main entry point for the Tennis Meetup Discord bot. It handles:
- Bot initialization and configuration
- Cog loading
- Event handling
- Command synchronization
- Logging setup

The bot is designed to manage a tennis community server with features for:
- Member onboarding
- Profile management
- Administrative functions
"""

import nextcord
from nextcord.ext import commands
import os
from dotenv import load_dotenv
import logging
from src.config.constants import TEST_GUILD_ID

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the bot with all necessary intents
intents = nextcord.Intents.default()
intents.members = True  # For tracking member joins/leaves
intents.message_content = True  # For reading message content
intents.guilds = True  # For guild-related features

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# List of cogs to load
initial_extensions = [
    'src.cogs.admin.admin',
    'src.cogs.user.welcome',
    'src.cogs.user.commands.wrapper'
]


@bot.slash_command(
    name="sync",
    description="Sync application commands",
    guild_ids=[TEST_GUILD_ID],
    default_member_permissions=nextcord.Permissions(administrator=True)
)
async def sync(interaction: nextcord.Interaction):
    """
    Synchronize application commands with Discord.

    This command forces an immediate synchronization of slash commands,
    making any command changes immediately available without the usual
    Discord cache delay.

    Args:
        interaction (nextcord.Interaction): The interaction object from Discord

    Note:
        - Only administrators can use this command
        - Useful when commands aren't appearing or updating
        - Primarily needed for global commands, not guild-specific ones
    """
    try:
        logger.info("Syncing application commands...")
        await interaction.response.defer()

        # Sync commands
        await bot.sync_application_commands()

        # Get and log synced commands
        commands = bot.get_application_commands()
        command_list = "\n".join([f"- /{cmd.name}" for cmd in commands])

        # Debug logging
        logger.debug(f"Synced commands: {command_list}")

        await interaction.followup.send(
            f"Successfully synced application commands!\n\nRegistered commands:\n{command_list}",
            ephemeral=True
        )
        logger.info("Application commands synced successfully")

    except Exception as e:
        logger.error(f"Error syncing commands: {e}", exc_info=True)
        await interaction.followup.send(
            f"Error syncing commands: {str(e)}",
            ephemeral=True
        )

@bot.event
async def on_ready():
    """
    Handle the bot's ready event.

    This event is triggered when the bot has successfully connected to Discord and is ready
    to receive commands. It performs initial setup tasks such as:
    - Logging bot status
    - Generating invite links
    - Debugging command registration
    """
    try:
        logger.info(f"Bot is ready! Logged in as {bot.user.name}")
        logger.info(f"Bot is in {len(bot.guilds)} guilds")
        logger.info(f"Test guild ID: {TEST_GUILD_ID}")

        # Generate invite link with required permissions and scopes
        permissions = nextcord.Permissions(administrator=True)
        scopes = ["bot", "applications.commands"]
        invite_link = nextcord.utils.oauth_url(
            bot.user.id,
            permissions=permissions,
            scopes=scopes
        )
        logger.info(f"\nUse this link to invite the bot:\n{invite_link}")

        # Debug: Log registered commands for each guild
        logger.debug("\nRegistered commands in guilds:")
        for guild in bot.guilds:
            try:
                # Get application commands using bot's method
                commands = bot.get_application_commands()
                logger.debug(f"\nCommands in {guild.name}:")
                for cmd in commands:
                    logger.debug(f"- {cmd.name}")
            except Exception as e:
                logger.error(f"Error fetching commands for {guild.name}: {e}", exc_info=True)

        # Debug: Log loaded cogs and their commands
        logger.debug("\nLoaded cogs and commands:")
        for cog_name, cog in bot.cogs.items():
            logger.debug(f"\nCog: {cog_name}")
            for command in cog.get_commands():
                logger.debug(f"- {command.name} ({type(command)})")


    except Exception as e:
        logger.error(f"Error in on_ready: {e}", exc_info=True)


@bot.event
async def on_application_command(interaction: nextcord.Interaction):
    """
    Log when slash commands are used.

    Args:
        interaction (nextcord.Interaction): The interaction object from Discord

    This event handler logs all slash command usage, with special handling for
    admin commands to include subcommand information.
    """
    try:
        command_name = interaction.data.get('name', 'unknown')
        if command_name == 'admin':
            subcommand = (
                interaction.data.get('options', [{}])[0].get('name', '')
                if interaction.data.get('options')
                else ''
            )
            logger.info(
                f"Admin command used: /admin {subcommand} by {interaction.user} "
                f"in {interaction.guild.name}/{interaction.channel.name}"
            )
        else:
            logger.info(
                f"Command used: /{command_name} by {interaction.user} "
                f"in {interaction.guild.name}/{interaction.channel.name}"
            )

    except Exception as e:
        logger.error(f"Error logging command usage: {e}", exc_info=True)


@bot.event
async def on_command_error(ctx, error):
    """
    Handle command errors globally.

    Args:
        ctx: The context in which the command was run
        error: The error that occurred

    This handler provides appropriate error messages for different types of
    command errors, with special handling for permission errors.
    """
    try:
        if isinstance(error, commands.errors.CommandNotFound):
            return  # Ignore command not found errors

        logger.error(f"Command error: {error}", exc_info=True)

        if isinstance(error, commands.errors.MissingPermissions):
            await ctx.send("You don't have permission to use this command.", ephemeral=True)
        else:
            await ctx.send(f"An error occurred: {str(error)}", ephemeral=True)

    except Exception as e:
        logger.error(f"Error handling command error: {e}", exc_info=True)


if __name__ == "__main__":
    # Load all cogs
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
            logger.info(f"Loaded {extension}")
            print(nextcord.__version__)
        except Exception as e:
            logger.error(f"Failed to load extension {extension}: {e}", exc_info=True)

    # Run the bot
    try:
        bot.run(os.getenv("TOKEN"))
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
