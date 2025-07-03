"""View for displaying currently playing users."""

import nextcord
import logging
from datetime import datetime
from typing import Dict, List, Tuple
from zoneinfo import ZoneInfo

from src.cogs.admin.dashboard.constants import EMBEDS, BUTTONS, TIME_FORMAT

logger = logging.getLogger(__name__)

class CurrentlyPlayingView(nextcord.ui.View):
    """View for displaying currently playing users by location."""

    def __init__(
        self,
        playing_data: Dict[str, List[Tuple[int, datetime, datetime]]],
        user_dict: Dict[int, Dict]
    ):
        """Initialize view with playing data.
        
        Args:
            playing_data (Dict): Dictionary mapping locations to lists of 
                                (user_id, start_time, end_time) tuples
            user_dict (Dict[int, Dict]): Dictionary mapping user IDs to user info
        """
        super().__init__(timeout=180)  # 3 minute timeout
        self.playing_data = playing_data
        self.user_dict = user_dict
        self.timezone = ZoneInfo("America/Vancouver")  # TODO: Make configurable

    async def get_embed(self) -> nextcord.Embed:
        """Get embed for currently playing users."""
        now = datetime.now(self.timezone)
        
        embed = nextcord.Embed(
            title=EMBEDS["PLAYING_TITLE"],
            description=f"{EMBEDS['PLAYING_DESCRIPTION']} ({now.strftime(TIME_FORMAT)})",
            color=0x00ff00
        )
        
        if not self.playing_data:
            embed.add_field(
                name="No Active Players",
                value="No players are currently active based on schedules.",
                inline=False
            )
            return embed
            
        # Add fields for each location
        for location, players in self.playing_data.items():
            if not players:
                continue
                
            # Format player list
            player_strings = []
            for user_id, start_time, end_time in players:
                user_info = self.user_dict.get(user_id, {})
                username = user_info.get("username", f"User {user_id}")
                rating = user_info.get("ntrp_rating", "N/A")
                
                # Format time remaining
                end_time_str = end_time.strftime(TIME_FORMAT)
                time_remaining = end_time - now
                minutes_remaining = int(time_remaining.total_seconds() / 60)
                
                if minutes_remaining <= 60:
                    time_str = f"Until {end_time_str} ({minutes_remaining} min remaining)"
                else:
                    time_str = f"Until {end_time_str}"
                
                player_strings.append(f"• {username} (NTRP {rating}): {time_str}")
            
            # Add field for this location
            embed.add_field(
                name=f"📍 {location} ({len(players)} player(s))",
                value="\n".join(player_strings),
                inline=False
            )
        
        # Add footer with timestamp
        embed.set_footer(text=f"Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        return embed

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
