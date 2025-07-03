# src/cogs/user/commands/get_started/dob_step.py
"""Implementation of the date of birth selection step."""

import re
import logging
from typing import Callable
import nextcord
from nextcord import Interaction, Embed, ui
from .constants import DOB_STEP, BUTTON_STYLES

logger = logging.getLogger(__name__)

class DateOfBirthModal(ui.Modal):
    """Modal for entering date of birth."""
    
    def __init__(self, callback_func: Callable[[Interaction, str], None]):
        super().__init__(title="Enter Date of Birth")
        self.callback_func = callback_func
        
        self.dob_input = ui.TextInput(
            label="Date of Birth (MM/DD/YYYY)",
            placeholder="e.g., 01/15/1990",
            required=True,
            max_length=10
        )
        self.add_item(self.dob_input)
    
    async def callback(self, interaction: Interaction):
        """Process the submitted date of birth."""
        dob = self.dob_input.value
        
        # Validate date format (MM/DD/YYYY)
        if not self._validate_date_format(dob):
            await interaction.response.send_message(
                "Please enter a valid date in MM/DD/YYYY format (e.g., 01/15/1990).",
                ephemeral=True
            )
            return
        
        await self.callback_func(interaction, dob)
    
    def _validate_date_format(self, date_str: str) -> bool:
        """Validate that the date string is in MM/DD/YYYY format."""
        pattern = r"^(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/\d{4}$"
        return bool(re.match(pattern, date_str))


class DateOfBirthView(nextcord.ui.View):
    """View for entering date of birth."""

    def __init__(self, callback: Callable[[Interaction, str], None]):
        super().__init__()
        self.callback = callback
        
        # Add button to open the modal
        enter_button = nextcord.ui.Button(
            style=BUTTON_STYLES["info"],
            label="Enter Date of Birth",
            emoji="📅",
            custom_id="enter_dob"
        )
        enter_button.callback = self._show_modal
        self.add_item(enter_button)
    
    async def _show_modal(self, interaction: Interaction):
        """Show the date of birth input modal."""
        modal = DateOfBirthModal(self.callback)
        await interaction.response.send_modal(modal)


async def dob_step(interaction: Interaction, callback: Callable[[Interaction, str], None]):
    """Show the date of birth selection step."""
    try:
        embed = Embed(
            title=DOB_STEP["title"],
            description=(
                f"{DOB_STEP['header']['emoji']} **{DOB_STEP['header']['title']}**\n"
                f"{DOB_STEP['header']['separator']}\n\n"
                f"{DOB_STEP['description']}"
            ),
            color=nextcord.Color.blue()
        )

        view = DateOfBirthView(callback)

        # Check if initial response has been made
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in date of birth step: {e}", exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "An error occurred. Please try again.",
                ephemeral=True
            )
