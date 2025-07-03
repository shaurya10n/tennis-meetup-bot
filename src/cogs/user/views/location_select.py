# src/cogs/user/views/location_select.py
"""Generic location selection view."""

import nextcord
from nextcord import Interaction, Embed, Color
import logging
from typing import List, Callable, Tuple
from src.cogs.user.commands.get_started.constants import BUTTON_STYLES

logger = logging.getLogger(__name__)

class LocationSelectView(nextcord.ui.View):
    """View for selecting locations."""

    def __init__(
        self,
        locations: List[Tuple[str, str]],  # List of (court_id, name) tuples
        callback: Callable[[Interaction, List[str]], None],
        step_config: dict,
        pre_selected_ids: List[str] = None,  # Parameter for pre-selected location IDs
        button_label: str = "Confirm"  # Parameter for custom button label, default to "Confirm" for consistency
    ):
        """Initialize the view.
        
        Args:
            locations (List[Tuple[str, str]]): List of (court_id, name) tuples
            callback (Callable): Function to call with selected location IDs
            step_config (dict): Configuration for this step from constants
            pre_selected_ids (List[str], optional): List of pre-selected location IDs
            button_label (str, optional): Label for the confirmation button. Defaults to "Confirm".
        """
        super().__init__()
        self.callback = callback
        self.selected_locations = set()
        self.locations = locations
        self.step_config = step_config
        
        # Map pre-selected IDs to indices
        if pre_selected_ids:
            for i, (court_id, _) in enumerate(locations):
                if court_id in pre_selected_ids:
                    self.selected_locations.add(i)

        for i, (court_id, name) in enumerate(locations):
            style = BUTTON_STYLES["selected"] if i in self.selected_locations else BUTTON_STYLES["unselected"]
            self.add_item(nextcord.ui.Button(
                label=name,
                custom_id=f"location_{i}",
                style=style,
                row=i // 3
            ))

        self.add_item(nextcord.ui.Button(
            label=button_label,
            custom_id="confirm_locations",
            style=BUTTON_STYLES["success"],
            row=(len(locations) // 3) + 1
        ))

    async def interaction_check(self, interaction: Interaction) -> bool:
        """Handle button interactions."""
        custom_id = interaction.data["custom_id"]

        if custom_id == "confirm_locations":
            if not self.selected_locations:
                await interaction.response.send_message(
                    "Please select at least one location.",
                    ephemeral=True
                )
                return False
            
            try:
                # Convert indexes to court IDs before sending
                selected_court_ids = [self.locations[i][0] for i in self.selected_locations]
                await self.callback(interaction, selected_court_ids)
                return True
            except Exception as e:
                # If the callback fails, log the error but don't try to respond again
                # as the interaction may have already been used
                logger.error(f"Error in location selection callback: {e}", exc_info=True)
                return False

        location_index = int(custom_id.split("_")[1])
        button = self.children[location_index]

        if location_index in self.selected_locations:
            self.selected_locations.remove(location_index)
            button.style = BUTTON_STYLES["unselected"]
        else:
            self.selected_locations.add(location_index)
            button.style = BUTTON_STYLES["selected"]

        await interaction.response.edit_message(view=self)
        return True

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

async def show_location_select(
    interaction: Interaction,
    locations: List[Tuple[str, str]],  # List of (court_id, name) tuples
    callback: Callable[[Interaction, List[str]], None],
    step_config: dict,
    pre_selected_ids: List[str] = None,  # Parameter for pre-selected location IDs
    button_label: str = "Confirm"  # Parameter for custom button label, default to "Confirm" for consistency
) -> None:
    """Show the location selection view.
    
    Args:
        interaction (Interaction): Discord interaction
        locations (List[Tuple[str, str]]): List of (court_id, name) tuples
        callback (Callable): Function to call with selected location IDs
        step_config (dict): Configuration for this step from constants
        pre_selected_ids (List[str], optional): List of pre-selected location IDs
        button_label (str, optional): Label for the confirmation button. Defaults to "Confirm".
    """
    try:
        if not locations:
            await interaction.response.send_message(
                "No locations available at the moment.",
                ephemeral=True
            )
            return

        view = LocationSelectView(
            locations=locations,
            callback=callback,
            step_config=step_config,
            pre_selected_ids=pre_selected_ids,
            button_label=button_label
        )
        
        embed = view.get_embed()

        # Check if initial response has been made
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in location select view: {e}", exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "An error occurred. Please try again.",
                ephemeral=True
            )
