"""View for displaying location availability."""

import nextcord
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from zoneinfo import ZoneInfo

from src.cogs.admin.dashboard.constants import EMBEDS, BUTTONS, TIME_FORMAT, DATE_FORMAT
from src.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class LocationAvailabilityView(nextcord.ui.View):
    """View for displaying player availability by location."""

    def __init__(
        self,
        location_data: Dict[str, Dict[str, List[Tuple[int, datetime, datetime]]]],
        user_dict: Dict[int, Dict],
        locations: List[str]
    ):
        """Initialize view with location data.
        
        Args:
            location_data (Dict): Dictionary mapping locations to date data
            user_dict (Dict[int, Dict]): Dictionary mapping user IDs to user info
            locations (List[str]): List of available locations
        """
        super().__init__(timeout=180)  # 3 minute timeout
        self.location_data = location_data
        self.user_dict = user_dict
        self.locations = locations
        self.current_location_index = 0
        config_loader = ConfigLoader()
        self.timezone = config_loader.get_timezone()
        
        # Update button states
        self._update_buttons()

    def _update_buttons(self):
        """Update button states based on current location."""
        self.previous_button.disabled = self.current_location_index == 0
        self.next_button.disabled = self.current_location_index >= len(self.locations) - 1

    def get_current_location(self) -> str:
        """Get the current location name."""
        if not self.locations:
            return "No Locations"
        return self.locations[self.current_location_index]

    async def get_embed(self) -> nextcord.Embed:
        """Get embed for current location's availability."""
        location = self.get_current_location()
        
        embed = nextcord.Embed(
            title=EMBEDS["LOCATION_TITLE"].format(location=location),
            description=EMBEDS["LOCATION_DESCRIPTION"].format(location=location),
            color=0x00ff00
        )
        
        # Get data for current location
        location_data = self.location_data.get(location, {})
        
        if not location_data:
            embed.add_field(
                name="No Data",
                value=EMBEDS["NO_DATA"],
                inline=False
            )
            return embed
            
        # Get dates in order
        dates = sorted(location_data.keys())
        
        # Convert dates to display format and create fields
        today = datetime.now(self.timezone).strftime("%Y-%m-%d")
        
        for date_str in dates:
            # Format date for display
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=self.timezone)
            display_date = date_obj.strftime(DATE_FORMAT)
            
            # Add "Today" marker if applicable
            if date_str == today:
                display_date = f"📅 {display_date} (Today)"
            
            # Build availability string for each time slot
            time_slots = location_data[date_str]
            slot_strings = []
            
            for slot_name in ["Morning", "Afternoon", "Evening"]:
                users = time_slots.get(slot_name, [])
                if not users:
                    slot_strings.append(f"**{slot_name}**: No players")
                    continue
                    
                # Format user list
                user_strings = []
                for user_id, start_time, end_time in users:
                    user_info = self.user_dict.get(user_id, {})
                    username = user_info.get("username", f"User {user_id}")
                    rating = user_info.get("ntrp_rating", "N/A")
                    user_strings.append(f"{username} (NTRP {rating})")
                
                slot_strings.append(f"**{slot_name}**: {len(users)} player(s)\n{', '.join(user_strings)}")
            
            # Add field for this date
            embed.add_field(
                name=display_date,
                value="\n\n".join(slot_strings),
                inline=False
            )
        
        # Add footer with navigation info
        embed.set_footer(text=f"Location {self.current_location_index + 1} of {len(self.locations)}")
        return embed

    @nextcord.ui.button(
        label=BUTTONS["PREVIOUS"],
        style=nextcord.ButtonStyle.gray,
        disabled=True
    )
    async def previous_button(
        self,
        button: nextcord.ui.Button,
        interaction: nextcord.Interaction
    ):
        """Handle previous location button click."""
        self.current_location_index = max(0, self.current_location_index - 1)
        self._update_buttons()
        await interaction.response.edit_message(
            embed=await self.get_embed(),
            view=self
        )

    @nextcord.ui.button(
        label=BUTTONS["NEXT"],
        style=nextcord.ButtonStyle.gray,
        disabled=True
    )
    async def next_button(
        self,
        button: nextcord.ui.Button,
        interaction: nextcord.Interaction
    ):
        """Handle next location button click."""
        self.current_location_index = min(len(self.locations) - 1, self.current_location_index + 1)
        self._update_buttons()
        await interaction.response.edit_message(
            embed=await self.get_embed(),
            view=self
        )

    @nextcord.ui.button(
        label=BUTTONS["REFRESH"],
        style=nextcord.ButtonStyle.green
    )
    async def refresh_button(
        self,
        button: nextcord.ui.Button,
        interaction: nextcord.Interaction
    ):
        """Handle refresh button click."""
        # In a real implementation, this would re-fetch the data
        # For now, we'll just refresh the display
        await interaction.response.edit_message(
            embed=await self.get_embed(),
            view=self
        )
