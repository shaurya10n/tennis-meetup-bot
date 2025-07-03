# src/cogs/user/views/interests_select.py
"""Generic interests selection view."""

import nextcord
from nextcord import Interaction, Embed, Color
import logging
from typing import List, Callable
from src.cogs.user.commands.get_started.constants import BUTTON_STYLES

logger = logging.getLogger(__name__)

class InterestsView(nextcord.ui.View):
    """View for selecting interests."""

    def __init__(
        self,
        callback: Callable[[Interaction, List[str]], None],
        step_config: dict,
        interest_options: dict,
        pre_selected_interests: List[str] = None,
        button_label: str = "Confirm"
    ):
        """Initialize the view.
        
        Args:
            callback (Callable): Function to call with selected interests
            step_config (dict): Configuration for this step from constants
            interest_options (dict): Dictionary of interest options
            pre_selected_interests (List[str], optional): List of pre-selected interests
            button_label (str, optional): Label for the confirmation button. Defaults to "Confirm".
        """
        super().__init__()
        self.callback = callback
        self.step_config = step_config
        self.interest_options = interest_options
        self.selected_interests = set(pre_selected_interests or [])
        self.button_label = button_label
        self._add_buttons()

    def _add_buttons(self):
        """Add buttons for each interest option."""
        # Add interest buttons
        for i, (interest_id, details) in enumerate(self.interest_options.items()):
            style = BUTTON_STYLES["selected"] if interest_id in self.selected_interests else BUTTON_STYLES["unselected"]
            button = nextcord.ui.Button(
                label=details["label"],
                emoji=details["emoji"],
                style=style,
                custom_id=f"interest_{interest_id}",
                row=i // 2
            )
            button.callback = lambda i, b=button, k=interest_id: self._handle_interest_click(i, b, k)
            self.add_item(button)

        # Add confirm button
        confirm_button = nextcord.ui.Button(
            label=self.button_label,
            style=BUTTON_STYLES["success"],
            custom_id="confirm_interests",
            row=(len(self.interest_options) // 2) + 1
        )
        confirm_button.callback = self._handle_confirm
        self.add_item(confirm_button)

    async def _handle_interest_click(self, interaction: Interaction, button: nextcord.ui.Button, interest_id: str):
        """Handle interest button selection."""
        try:
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

    async def _handle_confirm(self, interaction: Interaction):
        """Handle confirmation of selected interests."""
        if not self.selected_interests:
            await interaction.response.send_message(
                "Please select at least one interest!",
                ephemeral=True
            )
            return

        # Disable all buttons
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(view=self)
        await self.callback(interaction, list(self.selected_interests))

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

async def show_interests_select(
    interaction: Interaction,
    callback: Callable[[Interaction, List[str]], None],
    step_config: dict,
    interest_options: dict,
    pre_selected_interests: List[str] = None,
    button_label: str = "Confirm"
) -> None:
    """Show the interests selection view.
    
    Args:
        interaction (Interaction): Discord interaction
        callback (Callable): Function to call with selected interests
        step_config (dict): Configuration for this step from constants
        interest_options (dict): Dictionary of interest options
        pre_selected_interests (List[str], optional): List of pre-selected interests
        button_label (str, optional): Label for the confirmation button. Defaults to "Confirm".
    """
    try:
        view = InterestsView(
            callback=callback,
            step_config=step_config,
            interest_options=interest_options,
            pre_selected_interests=pre_selected_interests,
            button_label=button_label
        )
        
        embed = view.get_embed()

        # Check if initial response has been made
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in interests select view: {e}", exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "An error occurred. Please try again.",
                ephemeral=True
            )
