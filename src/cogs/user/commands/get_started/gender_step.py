# src/cogs/user/commands/get_started/gender_step.py
"""Implementation of the gender preference selection step."""

from typing import Callable
import nextcord
from nextcord import Interaction, Embed, ButtonStyle
from .constants import GENDER_STEP, GENDER_OPTIONS, BUTTON_STYLES


class GenderPreferenceView(nextcord.ui.View):
    """View for selecting gender preference."""

    def __init__(self, callback: Callable[[Interaction, str], None]):
        super().__init__()
        self.callback = callback
        self._add_buttons()

    def _add_buttons(self):
        """Add buttons for each gender option."""
        for key, option in GENDER_OPTIONS.items():
            button = nextcord.ui.Button(
                style=BUTTON_STYLES["unselected"],
                label=option["label"],
                emoji=option["emoji"],
                custom_id=f"gender_{key}"
            )
            button.callback = lambda i, b=button, v=option["value"]: self._handle_click(i, b, v)
            self.add_item(button)

    async def _handle_click(self, interaction: Interaction, button: nextcord.ui.Button, value: str):
        """Handle button click."""
        # Disable all buttons after selection
        for child in self.children:
            child.disabled = True
            if child.custom_id == button.custom_id:
                child.style = BUTTON_STYLES["selected"]

        await interaction.response.edit_message(view=self)
        await self.callback(interaction, value)


async def gender_preference_step(interaction: Interaction, callback: Callable[[Interaction, str], None]):
    """Show the gender preference selection step."""
    embed = Embed(
        title=GENDER_STEP["title"],
        description=(
            f"{GENDER_STEP['header']['emoji']} **{GENDER_STEP['header']['title']}**\n"
            f"{GENDER_STEP['header']['separator']}\n\n"
            f"{GENDER_STEP['description']}"
        ),
        color=nextcord.Color.blue()
    )

    view = GenderPreferenceView(callback)

    # Check if initial response has been made
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
