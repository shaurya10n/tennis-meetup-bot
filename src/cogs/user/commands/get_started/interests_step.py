# src/cogs/user/commands/get_started/interests_step.py
"""Interests selection step for the get-started command."""

import nextcord
from nextcord import Interaction
import logging
from .constants import INTEREST_STEP, INTEREST_OPTIONS, BUTTON_STYLES

logger = logging.getLogger(__name__)


class InterestsView(nextcord.ui.View):
    """Second step: Interests selection view."""

    def __init__(self, submit_callback):
        """Initialize interests selection view.

        Args:
            submit_callback: Callback function to handle profile submission
        """
        super().__init__()
        self.selected_interests = set()
        self.submit_callback = submit_callback

        # Add interest buttons
        for i, (interest_id, details) in enumerate(INTEREST_OPTIONS.items()):
            button = nextcord.ui.Button(
                label=details["label"],
                emoji=details["emoji"],
                style=BUTTON_STYLES["unselected"],
                custom_id=f"interest#{interest_id}",
                row=i // 2
            )
            button.callback = self.interest_button_callback
            self.add_item(button)

        # Add submit button
        submit_button = nextcord.ui.Button(
            label="Submit",
            style=BUTTON_STYLES["success"],
            row=2
        )
        submit_button.callback = self.submit_button_callback
        self.add_item(submit_button)

    async def interest_button_callback(self, interaction: Interaction):
        """Handle interest button selection."""
        try:
            custom_id = interaction.data.get('custom_id')
            if not custom_id:
                logger.error("No custom_id found in interaction data")
                return

            interest_id = custom_id.split("#")[1]
            button = next((b for b in self.children if b.custom_id == custom_id), None)

            if not button:
                logger.error(f"Button with custom_id {custom_id} not found")
                return

            if interest_id in self.selected_interests:
                self.selected_interests.remove(interest_id)
                button.style = BUTTON_STYLES["unselected"]
            else:
                self.selected_interests.add(interest_id)
                button.style = BUTTON_STYLES["selected"]

            await interaction.response.edit_message(view=self)
            logger.info(f"Interest toggled: {interest_id}")

        except Exception as e:
            logger.error(f"Error toggling interest: {e}", exc_info=True)
            await interaction.response.send_message(
                "An error occurred. Please try again.",
                ephemeral=True
            )

    async def submit_button_callback(self, interaction: Interaction):
        """Handle submit button click."""
        if not self.selected_interests:
            await interaction.response.send_message(
                "Please select at least one interest!",
                ephemeral=True
            )
            return

        await self.submit_callback(interaction, list(self.selected_interests))
