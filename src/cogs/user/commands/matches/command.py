"""Commands for managing tennis matches."""

import logging
from typing import Optional, List

import nextcord
from nextcord import Interaction, Embed, Color

from src.database.dao.dynamodb.match_dao import MatchDAO
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.database.models.dynamodb.match import Match
from src.utils.responses import Responses
from src.config.dynamodb_config import get_db
from .views import CompleteMatchView, CompleteMatchSelectionView, create_match_embed
from .constants import *

logger = logging.getLogger(__name__)


class MatchesCommand:
    """Commands for managing tennis matches."""
    
    def __init__(self):
        """Initialize the matches command handler."""
        self.dynamodb = get_db()
        self.match_dao = MatchDAO(self.dynamodb)
        self.player_dao = PlayerDAO(self.dynamodb)
        self.court_dao = CourtDAO(self.dynamodb)
        logger.info("Matches command handler initialized")
    
    async def matches_view(self, interaction: Interaction, view_type: str):
        """View completed or upcoming matches for the user.
        Args:
            interaction: Discord interaction
            view_type: 'completed' or 'upcoming'
        """
        try:
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id)
            if view_type == "completed":
                matches = self.match_dao.get_player_matches(guild_id, user_id, status="completed")
                title = "Completed Matches"
                empty_msg = "You don't have any completed matches yet."
                matches.sort(key=lambda m: m.start_time, reverse=True)
            else:
                matches = self.match_dao.get_player_matches(guild_id, user_id, status="scheduled")
                title = "Upcoming Matches"
                empty_msg = "You don't have any upcoming matches scheduled."
                matches.sort(key=lambda m: m.start_time)
            if not matches:
                await Responses.send_error(
                    interaction,
                    f"No {title}",
                    empty_msg
                )
                return
            embed = self._create_matches_list_embed(matches, title)
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error viewing {view_type} matches: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "View Failed",
                f"An error occurred while viewing your {view_type} matches. Please try again."
            )
    
    async def complete_match_selection(self, interaction: Interaction):
        """Show a list of scheduled matches for the user to complete.
        
        Args:
            interaction: Discord interaction
        """
        try:
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id)
            
            # Get scheduled matches for the user
            scheduled_matches = self.match_dao.get_player_matches(guild_id, user_id, status="scheduled")
            
            if not scheduled_matches:
                await Responses.send_error(
                    interaction,
                    "No Scheduled Matches",
                    "You don't have any scheduled matches to complete."
                )
                return
            
            # Sort by start time (earliest first)
            scheduled_matches.sort(key=lambda m: m.start_time)
            
            # Create view with match selection
            view = CompleteMatchSelectionView(scheduled_matches, self.match_dao, self.player_dao)
            
            embed = Embed(
                title="🎾 Complete Match",
                description=f"Select a match to complete from your {len(scheduled_matches)} scheduled match{'es' if len(scheduled_matches) != 1 else ''}:",
                color=Color.blue()
            )
            
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error showing match selection: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Selection Failed",
                "An error occurred while loading your matches. Please try again."
            )

    async def complete_match(self, interaction: Interaction, match_id: str):
        """Complete a specific match (legacy method for old command).
        
        Args:
            interaction: Discord interaction
            match_id: ID of the match to complete
        """
        try:
            # Get the match
            match = self.match_dao.get_match(str(interaction.guild.id), match_id)
            
            if not match:
                await Responses.send_error(
                    interaction,
                    "Match Not Found",
                    MATCH_NOT_FOUND
                )
                return
            
            # Check if match is already completed
            if match.status == "completed":
                await Responses.send_error(
                    interaction,
                    "Match Already Completed",
                    MATCH_ALREADY_COMPLETED
                )
                return
            
            # Check if match is in a state that can be completed
            if match.status not in ["scheduled", "in_progress"]:
                await Responses.send_error(
                    interaction,
                    "Match Not Ready",
                    MATCH_NOT_SCHEDULED
                )
                return
            
            # Check if user is a player in the match
            user_id = str(interaction.user.id)
            if user_id not in match.players:
                await Responses.send_error(
                    interaction,
                    "Not a Player",
                    PLAYER_NOT_IN_MATCH
                )
                return
            
            # Show completion view
            view = CompleteMatchView(match, self.match_dao)
            await interaction.response.send_message(
                "🎾 Complete Match\n\n1. Select the winner from the dropdown below\n2. Click 'Enter Match Details' to fill in the score and other details",
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error completing match: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Completion Failed",
                "An error occurred while completing the match. Please try again."
            )
    
    def _create_matches_list_embed(self, matches: List[Match], title: str) -> Embed:
        """Create an embed displaying a list of matches.
        
        Args:
            matches: List of matches to display
            title: Title for the embed
            
        Returns:
            Embed with match list
        """
        from datetime import datetime
        from nextcord import Color
        
        embed = Embed(
            title=f"🎾 {title}",
            description=f"Found {len(matches)} match{'es' if len(matches) != 1 else ''}",
            color=Color.blue()
        )
        
        for i, match in enumerate(matches[:10], 1):  # Show up to 10 matches
            # Get player names
            player_names = []
            for player_id in match.players:
                player = self.player_dao.get_player(str(match.guild_id), player_id)
                if player:
                    player_names.append(player.username)
                else:
                    player_names.append(f"Unknown Player ({player_id})")
            
            # Format players
            if match.match_type == "singles":
                players_text = f"{player_names[0]} vs {player_names[1]}"
            else:
                players_text = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
            
            # Format time
            start_time = datetime.fromtimestamp(match.start_time)
            end_time = datetime.fromtimestamp(match.end_time)
            time_text = f"{start_time.strftime('%A, %B %d at %I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            
            # Format court
            court_text = "TBD"
            if match.court_id:
                court = self.court_dao.get_court(match.court_id)
                if court:
                    court_text = court.name
            
            # Format score for completed matches
            score_text = "TBD"
            if match.status == "completed" and match.score:
                from .views import format_match_score
                score_text = format_match_score(match.score, match.match_type)
            
            # Create field value
            field_value = f"**Players:** {players_text}\n"
            field_value += f"**Time:** {time_text}\n"
            field_value += f"**Court:** {court_text}\n"
            field_value += f"**Score:** {score_text}\n"
            field_value += f"**Match ID:** `{match.match_id[:8]}...`"
            
            embed.add_field(
                name=f"Match {i}",
                value=field_value,
                inline=False
            )
        
        if len(matches) > 10:
            embed.add_field(
                name="Note",
                value=f"Showing first 10 matches. You have {len(matches) - 10} more match{'es' if len(matches) - 10 != 1 else ''}.",
                inline=False
            )
        
        return embed 