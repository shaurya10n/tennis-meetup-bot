# src/cogs/user/views/skill_level_select.py
"""Generic skill level selection view."""

import nextcord
from nextcord import Interaction, Embed, Color
import logging
from typing import List, Callable
from src.cogs.user.commands.get_started.constants import BUTTON_STYLES, SKILL_LEVEL_OPTIONS

logger = logging.getLogger(__name__)

class SkillLevelView(nextcord.ui.View):
    """View for selecting skill level preferences."""

    def __init__(
        self,
        callback: Callable[[Interaction, List[str]], None],
        step_config: dict,
        pre_selected_levels: List[str] = None,
        button_label: str = "Confirm"
    ):
        """Initialize the view.
        
        Args:
            callback (Callable): Function to call with selected skill levels
            step_config (dict): Configuration for this step from constants
            pre_selected_levels (List[str], optional): List of pre-selected skill levels
            button_label (str, optional): Label for the confirmation button. Defaults to "Confirm".
        """
        super().__init__()
        self.callback = callback
        self.selected_levels = set(pre_selected_levels or [])
        self.step_config = step_config
        self.button_label = button_label
        self._add_buttons()

    def _add_buttons(self):
        """Add buttons for each skill level option."""
        # Add option buttons
        for key, option in SKILL_LEVEL_OPTIONS.items():
            button = nextcord.ui.Button(
                style=BUTTON_STYLES["selected"] if key in self.selected_levels else BUTTON_STYLES["unselected"],
                label=option["label"],
                emoji=option["emoji"],
                custom_id=f"skill_level_{key}"
            )
            button.callback = lambda i, b=button, v=option["value"]: self._handle_option_click(i, b, v)
            self.add_item(button)

        # Add confirm button
        confirm_button = nextcord.ui.Button(
            style=BUTTON_STYLES["success"],
            label=self.button_label,
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

    def get_embed(self) -> Embed:
        """Get the embed for this view."""
        return Embed(
            title=self.step_config["title"],
            description=(
                f"{self.step_config['header']['emoji']} **{self.step_config['header']['title']}**\n"
                f"{self.step_config['header']['separator']}\n\n"
                f"{self.step_config['description']}"
            ),
            color=Color.blue()
        )

async def show_skill_level_select(
    interaction: Interaction,
    callback: Callable[[Interaction, List[str]], None],
    step_config: dict,
    pre_selected_levels: List[str] = None,
    button_label: str = "Confirm"
) -> None:
    """Show the skill level selection view.
    
    Args:
        interaction (Interaction): Discord interaction
        callback (Callable): Function to call with selected skill levels
        step_config (dict): Configuration for this step from constants
        pre_selected_levels (List[str], optional): List of pre-selected skill levels
        button_label (str, optional): Label for the confirmation button. Defaults to "Confirm".
    """
    try:
        view = SkillLevelView(
            callback=callback,
            step_config=step_config,
            pre_selected_levels=pre_selected_levels,
            button_label=button_label
        )
        
        embed = view.get_embed()

        # Check if initial response has been made
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in skill level select view: {e}", exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "An error occurred. Please try again.",
                ephemeral=True
            )
