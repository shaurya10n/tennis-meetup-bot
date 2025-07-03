# src/cogs/user/commands/get_started/ntrp/rating_select_step.py
import nextcord
from nextcord import Interaction, Embed, Color
import logging
from src.utils.responses import Responses
from ..constants import NTRP_RANGES, BUTTON_STYLES, NTRP_CONFIG

logger = logging.getLogger(__name__)


class NTRPSelectView(nextcord.ui.View):
    """View for selecting NTRP rating."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

        # Add rating buttons
        for rating_key, rating_info in NTRP_RANGES.items():
            button = nextcord.ui.Button(
                label=f"{rating_info['label']} ({rating_info['range']})",
                emoji=rating_info['emoji'],
                custom_id=f"ntrp-{rating_key}",
                style=BUTTON_STYLES["unselected"],
                row=len(self.children) // 3
            )
            button.callback = self.rating_callback
            self.add_item(button)

    async def rating_callback(self, interaction: Interaction):
        """Handle rating selection."""
        try:
            custom_id = interaction.data["custom_id"]
            rating_key = custom_id.split("-")[1]
            rating = NTRP_RANGES[rating_key]["value"]

            # Update button styles
            for child in self.children:
                if isinstance(child, nextcord.ui.Button):
                    child.style = BUTTON_STYLES["selected"] if child.custom_id == custom_id else BUTTON_STYLES[
                        "unselected"]

            # First, update the message to show selection
            await interaction.response.edit_message(view=self)

            # Then use a followup for the next step
            await self.callback(interaction, rating)

        except Exception as e:
            logger.error(f"Error in rating selection: {e}", exc_info=True)
            await interaction.followup.send(
                "An error occurred. Please try again.",
                ephemeral=True
            )


async def ntrp_select_step(interaction: Interaction, callback):
    """Present the NTRP rating selection step."""
    try:
        description = (
            "Select your current NTRP rating level. If you're between levels, "
            "select the lower rating.\n\n"
            "Your rating will be adjustable during a "
            f"{NTRP_CONFIG['calibration_period_days']}-day calibration period."
        )

        embed = Embed(
            title="Select Your NTRP Rating",
            description=description,
            color=Color.blue()
        )

        # Add descriptions for each rating level
        for rating_info in NTRP_RANGES.values():
            embed.add_field(
                name=f"{rating_info['emoji']} {rating_info['label']} ({rating_info['range']})",
                value=rating_info['description'],
                inline=False
            )

        view = NTRPSelectView(callback)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in ntrp_select_step: {e}", exc_info=True)
        await Responses.send_error(
            interaction,
            "Setup Error",
            "An error occurred. Please try again."
        )
