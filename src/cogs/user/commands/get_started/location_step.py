# src/cogs/user/commands/get_started/location_step.py

import nextcord
from nextcord import Interaction, Embed, Color
import logging
from src.utils.responses import Responses
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.config.dynamodb_config import get_db
from .constants import BUTTON_STYLES, LOCATION_STEP
from typing import List

logger = logging.getLogger(__name__)


class LocationSelectView(nextcord.ui.View):
    def __init__(self, locations: List[str], callback):
        super().__init__()
        self.callback = callback
        self.selected_locations = set()
        self.locations = locations  # Store the locations list

        for i, location in enumerate(locations):
            self.add_item(nextcord.ui.Button(
                label=location,
                custom_id=f"location_{i}",
                style=BUTTON_STYLES["unselected"],
                row=i // 3
            ))

        self.add_item(nextcord.ui.Button(
            label="Continue",
            custom_id="confirm_locations",
            style=BUTTON_STYLES["success"],
            row=(len(locations) // 3) + 1
        ))

    async def interaction_check(self, interaction: Interaction) -> bool:
        custom_id = interaction.data["custom_id"]

        if custom_id == "confirm_locations":
            if not self.selected_locations:
                await interaction.response.send_message(
                    "Please select at least one preferred location.",
                    ephemeral=True
                )
                return False
            # Convert indexes to actual location names before sending
            selected_location_names = [self.locations[i] for i in self.selected_locations]
            await self.callback(interaction, selected_location_names)
            return True

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


async def location_select_step(interaction: Interaction, callback):
    """Present the location selection step."""
    try:
        court_dao = CourtDAO(get_db())
        # Get all courts and extract unique locations
        courts = court_dao.list_courts()
        locations = list(set(court.location for court in courts))

        if not locations:
            await Responses.send_error(
                interaction,
                "No Locations Available",
                "There are no court locations available at the moment."
            )
            return

        embed = Embed(
            title=LOCATION_STEP["title"],
            description=(
                f"{LOCATION_STEP['header']['emoji']} **{LOCATION_STEP['header']['title']}**\n"
                f"{LOCATION_STEP['header']['separator']}\n\n"
                f"{LOCATION_STEP['description']}"
            ),
            color=Color.blue()
        )

        view = LocationSelectView(locations, callback)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in location select step: {e}", exc_info=True)
        await Responses.send_error(
            interaction,
            "Setup Error",
            "An error occurred. Please try again."
        )
