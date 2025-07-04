"""Commands for managing tennis matches."""

import logging
from typing import Optional

import nextcord
from nextcord import Interaction

from src.database.dao.dynamodb.match_dao import MatchDAO
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.utils.responses import Responses
from src.config.dynamodb_config import get_db
from .views import CompleteMatchModal, create_match_embed
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
    
    async def view_match(self, interaction: Interaction, match_id: str):
        """View details of a specific match.
        
        Args:
            interaction: Discord interaction
            match_id: ID of the match to view
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
            
            # Create and send the embed
            embed = create_match_embed(match, self.player_dao, self.court_dao)
            
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error viewing match: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "View Failed",
                "An error occurred while viewing the match. Please try again."
            )
    
    async def complete_match(self, interaction: Interaction, match_id: str):
        """Complete a match and record results.
        
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
            
            # Show completion modal
            modal = CompleteMatchModal(match, self.match_dao)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Error completing match: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Completion Failed",
                "An error occurred while completing the match. Please try again."
            ) 