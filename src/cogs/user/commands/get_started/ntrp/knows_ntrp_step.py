# src/cogs/user/commands/get_started/ntrp/knows_ntrp_step.py

import nextcord
from nextcord import Interaction, Embed, Color
import logging
from src.utils.responses import Responses
from ..constants import NTRP_STEP, NTRP_INFO, BUTTON_STYLES

logger = logging.getLogger(__name__)

class KnowsNTRPView(nextcord.ui.View):
    """View for asking if the user knows their NTRP rating."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

        # Add Yes/No buttons
        yes_button = nextcord.ui.Button(
            label="Yes, I know my rating",
            style=BUTTON_STYLES["success"],
            custom_id="knows_ntrp_yes"
        )
        yes_button.callback = self.button_callback

        no_button = nextcord.ui.Button(
            label="No, I need help",
            style=BUTTON_STYLES["unselected"],
            custom_id="knows_ntrp_no"
        )
        no_button.callback = self.button_callback

        info_button = nextcord.ui.Button(
            label="What's NTRP?",
            style=BUTTON_STYLES["info"],
            custom_id="ntrp_info"
        )
        info_button.callback = self.show_info

        self.add_item(yes_button)
        self.add_item(no_button)
        self.add_item(info_button)

    async def button_callback(self, interaction: Interaction):
        """Handle Yes/No button clicks."""
        try:
            custom_id = interaction.data["custom_id"]
            knows_ntrp = custom_id == "knows_ntrp_yes"
            await self.callback(interaction, knows_ntrp)
        except Exception as e:
            logger.error(f"Error in NTRP knowledge selection: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Error",
                "An error occurred. Please try again."
            )

    async def show_info(self, interaction: Interaction):
        """Show NTRP information popup."""
        embed = Embed(
            title="About NTRP Ratings",
            description=NTRP_INFO["description"],
            color=Color.blue()
        )
        embed.add_field(
            name="Learn More",
            value=f"[USTA NTRP Guidelines]({NTRP_INFO['help_link']})"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def knows_ntrp_step(interaction: Interaction, callback, custom_title=None, custom_description=None):
    """Present the initial NTRP knowledge question.
    
    Args:
        interaction (Interaction): Discord interaction
        callback: Function to call with user's response
        custom_title (str, optional): Custom title for the embed
        custom_description (str, optional): Custom description for the embed
    """
    try:
        title = custom_title or NTRP_STEP["title"]
        
        if custom_description:
            description = custom_description
        else:
            description = (
                f"{NTRP_STEP['header']['emoji']} **{NTRP_STEP['header']['title']}**\n"
                f"{NTRP_STEP['header']['separator']}\n\n"
                f"{NTRP_STEP['description']}\n\n"
                f"{NTRP_STEP['explanation']}"
            )
        
        embed = Embed(
            title=title,
            description=description,
            color=Color.blue()
        )

        view = KnowsNTRPView(callback)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in knows_ntrp_step: {e}", exc_info=True)
        await Responses.send_error(
            interaction,
            "Setup Error",
            "An error occurred. Please try again."
        )
