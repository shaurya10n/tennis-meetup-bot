# src/cogs/user/commands/get_started/ntrp/rating_confirm_step.py

import nextcord
from nextcord import Interaction, Embed, Color
import logging
from src.utils.responses import Responses
from ..constants import BUTTON_STYLES

logger = logging.getLogger(__name__)


class RatingConfirmView(nextcord.ui.View):
    def __init__(self, callback, current_rating: float):
        super().__init__()
        self.callback = callback
        self.current_rating = current_rating

        # Add adjustment buttons
        self.add_item(nextcord.ui.Button(
            label="↓ Lower (0.5)",
            custom_id="adjust_down",
            style=BUTTON_STYLES["unselected"]
        ))
        self.add_item(nextcord.ui.Button(
            label="Confirm",
            custom_id="confirm",
            style=BUTTON_STYLES["success"]
        ))
        self.add_item(nextcord.ui.Button(
            label="↑ Higher (0.5)",
            custom_id="adjust_up",
            style=BUTTON_STYLES["unselected"]
        ))

    async def interaction_check(self, interaction: Interaction) -> bool:
        """Handle button interactions."""
        custom_id = interaction.data.get("custom_id")

        if custom_id == "confirm":
            # First edit the message to show confirmation
            await interaction.response.edit_message(
                content=f"Rating confirmed: {self.current_rating}",
                view=None
            )
            # Then use followup for the next step
            await self.callback(interaction, self.current_rating)
        elif custom_id == "adjust_up":
            self.current_rating += 0.5
            await self.update_message(interaction)
        elif custom_id == "adjust_down":
            self.current_rating -= 0.5
            await self.update_message(interaction)

        return True

    async def update_message(self, interaction: Interaction):
        """Update the message with new rating."""
        embed = get_confirmation_embed(self.current_rating)
        await interaction.response.edit_message(embed=embed, view=self)



def get_confirmation_embed(rating: float) -> Embed:
    """Create embed for rating confirmation."""
    return Embed(
        title="Confirm Your NTRP Rating",
        description=(
            f"Based on your responses, your NTRP rating is: **{rating}**\n\n"
            "You can adjust this rating slightly if you feel it's not accurate.\n"
            "This rating will be adjustable during a 2-week calibration period."
        ),
        color=Color.blue()
    )


async def rating_confirm_step(interaction: Interaction, rating: float, callback):
    """Present the rating confirmation step."""
    try:
        embed = get_confirmation_embed(rating)
        view = RatingConfirmView(callback, rating)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in rating confirmation: {e}", exc_info=True)
        await Responses.send_error(
            interaction,
            "Confirmation Error",
            "An error occurred. Please try again."
        )
