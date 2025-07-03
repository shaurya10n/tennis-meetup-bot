# src/cogs/user/views/gender_select.py
"""Generic gender preference selection view."""

import nextcord
from nextcord import Interaction, Embed, Color
import logging
from typing import Callable, List
from src.cogs.user.commands.get_started.constants import BUTTON_STYLES, GENDER_OPTIONS

logger = logging.getLogger(__name__)

class GenderPreferenceView(nextcord.ui.View):
    """View for selecting gender preference."""

    def __init__(
        self,
        callback: Callable[[Interaction, List[str]], None],
        step_config: dict,
        pre_selected_preferences: List[str] = None,
        button_label: str = "Submit"
    ):
        """Initialize the view.
        
        Args:
            callback (Callable): Function to call with selected gender preferences
            step_config (dict): Configuration for this step from constants
            pre_selected_preferences (List[str], optional): Currently selected preferences
            button_label (str, optional): Label for the submit button
        """
        super().__init__()
        self.callback = callback
        self.step_config = step_config
        self.selected_preferences = pre_selected_preferences or []
        self.button_label = button_label
        self._add_buttons()

    def _add_buttons(self):
        """Add buttons for each gender option."""
        # Add gender option buttons
        for key, option in GENDER_OPTIONS.items():
            is_selected = key in self.selected_preferences
            button = nextcord.ui.Button(
                style=BUTTON_STYLES["selected"] if is_selected else BUTTON_STYLES["unselected"],
                label=option["label"],
                emoji=option["emoji"],
                custom_id=f"gender_{key}"
            )
            button.callback = lambda i, k=key, b=button: self._handle_click(i, k, b)
            self.add_item(button)
        
        # Add submit button in a new row
        submit_button = nextcord.ui.Button(
            style=BUTTON_STYLES["success"],
            label=self.button_label,
            custom_id="gender_submit",
            row= len(GENDER_OPTIONS) // 3 + 1
        )
        submit_button.callback = self._handle_submit
        self.add_item(submit_button)

    async def _handle_click(self, interaction: Interaction, key: str, button: nextcord.ui.Button):
        """Handle button click to toggle selection."""
        # Toggle selection
        if key in self.selected_preferences:
            self.selected_preferences.remove(key)
            button.style = BUTTON_STYLES["unselected"]
            logger.info(f"Removed {key} from selected preferences: {self.selected_preferences}")
        else:
            self.selected_preferences.append(key)
            button.style = BUTTON_STYLES["selected"]
            logger.info(f"Added {key} to selected preferences: {self.selected_preferences}")
        
        await interaction.response.edit_message(view=self)

    async def _handle_submit(self, interaction: Interaction):
        """Handle submit button click."""
        # If no selections, default to "none"
        if not self.selected_preferences:
            self.selected_preferences = ["none"]
            logger.info("No preferences selected, defaulting to ['none']")
        else:
            logger.info(f"Submitting selected preferences: {self.selected_preferences}")
        
        # Disable all buttons
        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(view=self)
        await self.callback(interaction, self.selected_preferences)

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

async def show_gender_select(
    interaction: Interaction,
    callback: Callable[[Interaction, List[str]], None],
    step_config: dict,
    pre_selected_preferences: List[str] = None,
    button_label: str = "Submit"
) -> None:
    """Show the gender preference selection view.
    
    Args:
        interaction (Interaction): Discord interaction
        callback (Callable): Function to call with selected gender preferences
        step_config (dict): Configuration for this step from constants
        pre_selected_preferences (List[str], optional): Currently selected preferences
        button_label (str, optional): Label for the submit button
    """
    try:
        # Log the incoming pre-selected preferences
        logger.info(f"Incoming pre_selected_preferences: {pre_selected_preferences} (type: {type(pre_selected_preferences).__name__})")
        
        # Convert single preference to list for backward compatibility
        if isinstance(pre_selected_preferences, str):
            pre_selected_preferences = [pre_selected_preferences] if pre_selected_preferences else []
            logger.info(f"Converted string preference to list: {pre_selected_preferences}")
        
        view = GenderPreferenceView(
            callback=callback,
            step_config=step_config,
            pre_selected_preferences=pre_selected_preferences,
            button_label=button_label
        )
        
        embed = view.get_embed()

        # Check if initial response has been made
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in gender preference select view: {e}", exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "An error occurred. Please try again.",
                ephemeral=True
            )
