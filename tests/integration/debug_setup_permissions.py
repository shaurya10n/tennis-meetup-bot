# debug_bot.py
import os
from dotenv import load_dotenv
import nextcord
from nextcord.ext import commands
import logging
from src.cogs.admin.setup.command_permissions import CommandPermissionSetup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DEV_GUILD_ID = int(os.getenv("TEST_GUILD_ID"))


class DebugBot(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Called when the bot is starting."""
        # Breakpoint 1: Inspect bot initialization
        logger.info(f"Bot is ready: {self.user}")

        # Sync commands with Discord
        logger.info("Syncing commands...")
        guild = self.get_guild(DEV_GUILD_ID)
        if guild:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Commands synced to guild: {guild.name}")

            # Log all commands
            commands = await guild.fetch_application_commands()
            for cmd in commands:
                logger.info(f"Registered command: /{cmd.name}")
        else:
            logger.error(f"Could not find guild with ID {DEV_GUILD_ID}")

    @nextcord.slash_command(name="debug_permissions", description="Debug command permissions setup",
                            guild_ids=[DEV_GUILD_ID])
    async def debug_permissions(self, interaction: nextcord.Interaction):
        """Debug command permissions setup"""
        try:
            await interaction.response.defer()  # Acknowledge the interaction first

            # Breakpoint 2: Inspect interaction
            logger.info(f"Received interaction from {interaction.user}")

            # Breakpoint 3: Inspect guild
            guild = interaction.guild
            logger.info(f"Guild: {guild.name}")

            # Breakpoint 4: Inspect command_permissions initialization
            command_permissions = CommandPermissionSetup(self)

            # Breakpoint 5: Before setup
            await command_permissions.setup_command_permissions(interaction)

            await interaction.followup.send("Debug complete!")

        except Exception as e:
            logger.error(f"Debug failed: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message("Debug failed!", ephemeral=True)
            else:
                await interaction.followup.send("Debug failed!", ephemeral=True)


bot = DebugBot()

# Run the bot
if __name__ == "__main__":
    logger.info("Starting bot...")
    bot.run(os.getenv("TOKEN"))
