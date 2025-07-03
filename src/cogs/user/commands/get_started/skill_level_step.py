# src/cogs/user/commands/get_started/skill_level_step.py
"""Implementation of the skill level preference selection step."""

from typing import Callable, List
import nextcord
from nextcord import Interaction, Embed, ButtonStyle
from .constants import SKILL_LEVEL_STEP, SKILL_LEVEL_OPTIONS, BUTTON_STYLES


class SkillLevelView(nextcord.ui.View):
    """View for selecting skill level preferences."""

    def __init__(self, callback: Callable[[Interaction, List[str]], None]):
        super().__init__()
        self.callback = callback
        self.selected_levels = set()
        self._add_buttons()

    def _add_buttons(self):
        """Add buttons for each skill level option."""
        # Add option buttons
        for key, option in SKILL_LEVEL_OPTIONS.items():
            button = nextcord.ui.Button(
                style=BUTTON_STYLES["unselected"],
                label=option["label"],
                emoji=option["emoji"],
                custom_id=f"skill_level_{key}"
            )
            button.callback = lambda i, b=button, v=option["value"]: self._handle_option_click(i, b, v)
            self.add_item(button)

        # Add confirm button
        confirm_button = nextcord.ui.Button(
            style=BUTTON_STYLES["success"],
            label="Continue",
            custom_id="confirm_skill_levels",
            row=len(SKILL_LEVEL_OPTIONS) // 3 + 1
        )
        confirm_button.callback = self._handle_confirm
        self.add_item(confirm_button)

    async def _handle_option_click(self, interaction: Interaction, button: nextcord.ui.Button, value: str):
        """Handle skill level option selection."""
        if value in self.selected_levels:
            self.selected_levels.remove(value)
            button.style = BUTTON_STYLES["unselected"]
        else:
            self.selected_levels.add(value)
            button.style = BUTTON_STYLES["selected"]

        await interaction.response.edit_message(view=self)

    async def _handle_confirm(self, interaction: Interaction):
        """Handle confirmation of selected skill levels."""
        if not self.selected_levels:
            await interaction.response.send_message(
                "Please select at least one skill level preference.",
                ephemeral=True
            )
            return

        # Disable all buttons
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(view=self)
        await self.callback(interaction, list(self.selected_levels))


async def skill_level_step(interaction: Interaction, callback: Callable[[Interaction, List[str]], None]):
    """Show the skill level preference selection step."""
    embed = Embed(
        title=SKILL_LEVEL_STEP["title"],
        description=(
            f"{SKILL_LEVEL_STEP['header']['emoji']} **{SKILL_LEVEL_STEP['header']['title']}**\n"
            f"{SKILL_LEVEL_STEP['header']['separator']}\n\n"
            f"{SKILL_LEVEL_STEP['description']}"
        ),
        color=nextcord.Color.blue()
    )

    view = SkillLevelView(callback)

    # Check if initial response has been made
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
