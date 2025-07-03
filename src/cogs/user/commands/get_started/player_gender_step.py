# src/cogs/user/commands/get_started/player_gender_step.py
"""Implementation of the player gender selection step."""

from typing import Callable
import nextcord
from nextcord import Interaction, Embed
from .constants import PLAYER_GENDER_STEP, PLAYER_GENDER_OPTIONS, BUTTON_STYLES


class PlayerGenderView(nextcord.ui.View):
    """View for selecting player's gender."""

    def __init__(self, callback: Callable[[Interaction, str], None]):
        super().__init__()
        self.callback = callback
        self._add_buttons()

    def _add_buttons(self):
        """Add buttons for each gender option."""
        for key, option in PLAYER_GENDER_OPTIONS.items():
            button = nextcord.ui.Button(
                style=BUTTON_STYLES["unselected"],
                label=option["label"],
                emoji=option["emoji"],
                custom_id=f"player_gender_{key}"
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


async def player_gender_step(interaction: Interaction, callback: Callable[[Interaction, str], None]):
    """Show the player gender selection step."""
    embed = Embed(
        title=PLAYER_GENDER_STEP["title"],
        description=(
            f"{PLAYER_GENDER_STEP['header']['emoji']} **{PLAYER_GENDER_STEP['header']['title']}**\n"
            f"{PLAYER_GENDER_STEP['header']['separator']}\n\n"
            f"{PLAYER_GENDER_STEP['description']}"
        ),
        color=nextcord.Color.blue()
    )

    view = PlayerGenderView(callback)

    # Check if initial response has been made
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
