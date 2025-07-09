"""Views for matches commands."""

import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal

import nextcord
from nextcord import Interaction, Embed, Color, ButtonStyle, TextInputStyle
from nextcord.ui import View, Button, Modal, TextInput, Select

from src.database.models.dynamodb.match import Match
from src.database.dao.dynamodb.match_dao import MatchDAO
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.utils.responses import Responses
from .constants import *

logger = logging.getLogger(__name__)


class CompleteMatchView(View):
    """View for completing a match with results."""
    
    def __init__(self, match: Match, match_dao: MatchDAO):
        """Initialize the completion view.
        
        Args:
            match: The match to complete
            match_dao: Match data access object
        """
        super().__init__(timeout=300)
        self.match = match
        self.match_dao = match_dao
        
        # Create winner select dropdown
        from src.database.dao.dynamodb.player_dao import PlayerDAO
        from src.config.dynamodb_config import get_db
        player_dao = PlayerDAO(get_db())
        options = []
        for player_id in self.match.players:
            player = player_dao.get_player(str(self.match.guild_id), player_id)
            if player:
                options.append(nextcord.SelectOption(label=player.username, value=player_id))
            else:
                options.append(nextcord.SelectOption(label=f"Unknown Player ({player_id})", value=player_id))
        
        self.winner_select = Select(
            placeholder="Select the winner",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="winner_select"
        )
        self.add_item(self.winner_select)
        
        # Add button to open score modal
        self.add_item(CompleteMatchButton())
    
    async def interaction_check(self, interaction: Interaction) -> bool:
        """Handle select interaction."""
        if interaction.data.get("custom_id") == "winner_select":
            # Store the selected winner
            self.selected_winner = interaction.data["values"][0]
            await interaction.response.send_message(
                f"✅ Winner selected! Now click 'Enter Match Details' to complete the form.",
                ephemeral=True
            )
            return False
        return True


class CompleteMatchButton(Button):
    """Button to open the match completion modal."""
    
    def __init__(self):
        super().__init__(
            label="Enter Match Details",
            style=ButtonStyle.primary,
            custom_id="complete_match_button"
        )
    
    async def callback(self, interaction: Interaction):
        """Open the completion modal."""
        view = self.view
        if not hasattr(view, 'selected_winner'):
            await interaction.response.send_message(
                "❌ Please select a winner first!",
                ephemeral=True
            )
            return
        
        # Create and show the modal
        modal = CompleteMatchModal(view.match, view.match_dao, view.selected_winner)
        await interaction.response.send_modal(modal)


class CompleteMatchModal(Modal):
    """Modal for completing a match with results."""
    
    def __init__(self, match: Match, match_dao: MatchDAO, winner_id: str):
        """Initialize the completion modal.
        
        Args:
            match: The match to complete
            match_dao: Match data access object
            winner_id: Pre-selected winner ID
        """
        super().__init__(title="Complete Match", timeout=300)
        self.match = match
        self.match_dao = match_dao
        self.winner_id = winner_id
        
        # Score input
        self.score_input = TextInput(
            label="Match Score",
            placeholder="6-4, 6-2 (singles) or 6-4, 6-2, 6-4 (doubles)",
            style=TextInputStyle.short,
            required=True,
            max_length=50
        )
        self.add_item(self.score_input)
        
        # Quality score input
        self.quality_input = TextInput(
            label="Match Quality (1-10)",
            placeholder="Rate the match quality from 1-10",
            style=TextInputStyle.short,
            required=False,
            max_length=2
        )
        self.add_item(self.quality_input)
        
        # Notes input
        self.notes_input = TextInput(
            label="Match Notes (optional)",
            placeholder="Any additional notes about the match",
            style=TextInputStyle.paragraph,
            required=False,
            max_length=500
        )
        self.add_item(self.notes_input)
    
    async def callback(self, interaction: Interaction):
        """Handle modal submission."""
        try:
            # Parse score
            score_text = self.score_input.value.strip()
            score = self._parse_score(score_text)
            if not score:
                await Responses.send_error(
                    interaction,
                    "Invalid Score Format",
                    INVALID_SCORE_FORMAT
                )
                return
            
            # Get winner username
            from src.database.dao.dynamodb.player_dao import PlayerDAO
            from src.config.dynamodb_config import get_db
            player_dao = PlayerDAO(get_db())
            winner_player = player_dao.get_player(str(self.match.guild_id), self.winner_id)
            winner_username = winner_player.username if winner_player else self.winner_id
            
            # Parse quality score
            quality_score = None
            if self.quality_input.value.strip():
                try:
                    quality_score = Decimal(self.quality_input.value.strip())
                    if not (1 <= quality_score <= 10):
                        await Responses.send_error(
                            interaction,
                            "Invalid Quality Score",
                            INVALID_QUALITY_SCORE
                        )
                        return
                except (ValueError, TypeError):
                    await Responses.send_error(
                        interaction,
                        "Invalid Quality Score",
                        INVALID_QUALITY_SCORE
                    )
                    return
            
            # Get notes
            notes = self.notes_input.value.strip() if self.notes_input.value else None
            
            # Complete the match
            updated_match = self.match_dao.update_match(
                str(interaction.guild.id),
                self.match.match_id,
                status="completed",
                score=score,
                winner=self.winner_id,
                match_quality_score=quality_score,
                notes=notes
            )
            
            if not updated_match:
                await Responses.send_error(
                    interaction,
                    "Update Failed",
                    "Failed to update match. Please try again."
                )
                return
            
            # Create success embed
            embed = create_match_completion_embed(updated_match, winner_username)
            
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error completing match: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Completion Failed",
                "An error occurred while completing the match. Please try again."
            )
    
    def _parse_score(self, score_text: str) -> Optional[Dict[str, Any]]:
        """Parse score text into structured format.
        
        Args:
            score_text: Score text like "6-4, 6-2" or "6-4, 6-2, 6-4"
            
        Returns:
            Dict with score structure or None if invalid
        """
        try:
            # Remove extra spaces and split by comma
            sets = [s.strip() for s in score_text.split(',')]
            
            if len(sets) < 2:
                return None
            
            parsed_sets = []
            for set_score in sets:
                # Match pattern like "6-4" or "7-5"
                match = re.match(r'^(\d+)-(\d+)$', set_score)
                if not match:
                    return None
                
                games1, games2 = int(match.group(1)), int(match.group(2))
                if games1 < 0 or games2 < 0:
                    return None
                
                parsed_sets.append({
                    'player1_games': games1,
                    'player2_games': games2
                })
            
            # For doubles, we need at least 3 sets (best of 3)
            if self.match.match_type == "doubles" and len(parsed_sets) < 3:
                return None
            
            return {
                'sets': parsed_sets,
                'total_sets': len(parsed_sets)
            }
            
        except Exception:
            return None
    
    def _find_winner_id(self, username: str) -> Optional[str]:
        """Find user ID by username from match players.
        
        Args:
            username: Username to find
            
        Returns:
            User ID if found, None otherwise
        """
        # Look up the player by username in the database
        from src.database.dao.dynamodb.player_dao import PlayerDAO
        from src.config.dynamodb_config import get_db
        
        player_dao = PlayerDAO(get_db())
        
        # Check each player in the match
        for player_id in self.match.players:
            player = player_dao.get_player(str(self.match.guild_id), player_id)
            if player and player.username.lower() == username.lower():
                return player_id
        
        return None


class CompleteMatchSelectionView(View):
    """View for selecting a match to complete."""
    
    def __init__(self, matches: List[Match], match_dao: MatchDAO, player_dao: PlayerDAO):
        """Initialize the selection view.
        
        Args:
            matches: List of scheduled matches
            match_dao: Match data access object
            player_dao: Player data access object
        """
        super().__init__(timeout=300)
        self.matches = matches
        self.match_dao = match_dao
        self.player_dao = player_dao
        
        # Create match selection dropdown
        options = []
        for match in matches:
            # Get player names for the match
            player_names = []
            for player_id in match.players:
                player = player_dao.get_player(str(match.guild_id), player_id)
                if player:
                    player_names.append(player.username)
                else:
                    player_names.append(f"Unknown Player ({player_id})")
            
            # Format match description
            if match.match_type == "singles":
                match_desc = f"{player_names[0]} vs {player_names[1]}"
            else:
                match_desc = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
            
            # Add time info
            start_time = datetime.fromtimestamp(match.start_time)
            time_str = start_time.strftime('%A, %B %d at %I:%M %p')
            label = f"{match_desc} - {time_str}"
            
            # Truncate if too long (Discord limit is 100 characters)
            if len(label) > 100:
                label = label[:97] + "..."
            
            options.append(nextcord.SelectOption(
                label=label,
                value=match.match_id,
                description=f"Match ID: {match.match_id[:8]}..."
            ))
        
        self.match_select = Select(
            placeholder="Select a match to complete",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="match_select"
        )
        self.add_item(self.match_select)
    
    async def interaction_check(self, interaction: Interaction) -> bool:
        """Handle select interaction."""
        if interaction.data.get("custom_id") == "match_select":
            selected_match_id = interaction.data["values"][0]
            
            # Find the selected match
            selected_match = None
            for match in self.matches:
                if match.match_id == selected_match_id:
                    selected_match = match
                    break
            
            if not selected_match:
                await interaction.response.send_message(
                    "❌ Selected match not found. Please try again.",
                    ephemeral=True
                )
                return False
            
            # Check if user is a player in the match
            user_id = str(interaction.user.id)
            if user_id not in selected_match.players:
                await interaction.response.send_message(
                    "❌ You are not a player in this match.",
                    ephemeral=True
                )
                return False
            
            # Show completion view for the selected match
            completion_view = CompleteMatchView(selected_match, self.match_dao)
            await interaction.response.send_message(
                f"🎾 Complete Match\n\n**Selected:** {selected_match.match_id[:8]}...\n\n1. Select the winner from the dropdown below\n2. Click 'Enter Match Details' to fill in the score and other details",
                view=completion_view,
                ephemeral=True
            )
            return False
        
        return True


def create_match_embed(match: Match, player_dao: PlayerDAO, court_dao: CourtDAO) -> Embed:
    """Create an embed displaying match details.
    
    Args:
        match: The match to display
        player_dao: Player data access object
        court_dao: Court data access object
        
    Returns:
        Embed with match details
    """
    # Set color based on status
    color_map = {
        "scheduled": EMBED_COLOR_SCHEDULED,
        "in_progress": EMBED_COLOR_IN_PROGRESS,
        "completed": EMBED_COLOR_COMPLETED,
        "cancelled": EMBED_COLOR_CANCELLED
    }
    color = color_map.get(match.status, Color.default())
    
    embed = Embed(
        title=f"🎾 Match Details - {match.match_id[:8]}...",
        description=f"**Status:** {match.status.replace('_', ' ').title()}",
        color=color
    )
    
    # Players
    player_names = []
    for player_id in match.players:
        player = player_dao.get_player(str(match.guild_id), player_id)
        if player:
            player_names.append(player.username)
        else:
            player_names.append(f"Unknown Player ({player_id})")
    
    if match.match_type == "singles":
        players_text = f"{player_names[0]} vs {player_names[1]}"
    else:
        players_text = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
    
    embed.add_field(
        name="Players",
        value=players_text,
        inline=True
    )
    
    # Match type
    embed.add_field(
        name="Type",
        value=match.match_type.title(),
        inline=True
    )
    
    # Time
    if match.start_time and match.end_time:
        start_time = datetime.fromtimestamp(match.start_time)
        end_time = datetime.fromtimestamp(match.end_time)
        duration = match.get_duration_minutes()
        
        time_text = (
            f"**Start:** {start_time.strftime('%A, %B %d at %I:%M %p')}\n"
            f"**End:** {end_time.strftime('%I:%M %p')}\n"
            f"**Duration:** {duration} minutes"
        )
    else:
        time_text = "Time not set"
    
    embed.add_field(
        name="Time",
        value=time_text,
        inline=False
    )
    
    # Court
    if match.court_id:
        court = court_dao.get_court(match.court_id)
        court_text = court.name if court else f"Court {match.court_id}"
    else:
        court_text = "Court TBD"
    
    embed.add_field(
        name="Court",
        value=court_text,
        inline=True
    )
    
    # NTRP Ratings
    if match.player_ratings:
        ratings_text = []
        for player_id, rating in match.player_ratings.items():
            player = player_dao.get_player(str(match.guild_id), player_id)
            name = player.username if player else f"Player {player_id}"
            ratings_text.append(f"{name}: {float(rating)}")
        
        embed.add_field(
            name="NTRP Ratings",
            value="\n".join(ratings_text),
            inline=True
        )
    
    # Score
    if match.status == "completed" and match.score:
        score_text = format_match_score(match.score, match.match_type)
        embed.add_field(
            name="Score",
            value=score_text,
            inline=True
        )
        
        # Winner
        if match.winner:
            winner_player = player_dao.get_player(str(match.guild_id), match.winner)
            winner_name = winner_player.username if winner_player else f"Player {match.winner}"
            embed.add_field(
                name="Winner",
                value=winner_name,
                inline=True
            )
    else:
        # Show placeholder for scheduled matches
        embed.add_field(
            name="Score",
            value="TBD",
            inline=True
        )
        
        embed.add_field(
            name="Winner",
            value="TBD",
            inline=True
        )
    
    # Quality score
    if match.match_quality_score:
        embed.add_field(
            name="Match Quality",
            value=f"{float(match.match_quality_score)}/10",
            inline=True
        )
    
    # Notes
    if match.notes:
        embed.add_field(
            name="Notes",
            value=match.notes,
            inline=False
        )
    
    # Timestamps
    created_at = datetime.fromisoformat(match.created_at.replace('Z', '+00:00'))
    updated_at = datetime.fromisoformat(match.updated_at.replace('Z', '+00:00'))
    
    embed.add_field(
        name="Created",
        value=created_at.strftime('%B %d, %Y at %I:%M %p'),
        inline=True
    )
    
    embed.add_field(
        name="Last Updated",
        value=updated_at.strftime('%B %d, %Y at %I:%M %p'),
        inline=True
    )
    
    return embed


def create_match_completion_embed(match: Match, winner_name: str) -> Embed:
    """Create an embed for match completion confirmation.
    
    Args:
        match: The completed match
        winner_name: Name of the winner
        
    Returns:
        Embed confirming match completion
    """
    embed = Embed(
        title="✅ Match Completed!",
        description=MATCH_COMPLETED_SUCCESS,
        color=Color.green()
    )
    
    # Score
    if match.score:
        score_text = format_match_score(match.score, match.match_type)
        embed.add_field(
            name="Final Score",
            value=score_text,
            inline=True
        )
    
    # Winner
    embed.add_field(
        name="Winner",
        value=winner_name,
        inline=True
    )
    
    # Quality score
    if match.match_quality_score:
        embed.add_field(
            name="Match Quality",
            value=f"{float(match.match_quality_score)}/10",
            inline=True
        )
    
    # Notes
    if match.notes:
        embed.add_field(
            name="Notes",
            value=match.notes,
            inline=False
        )
    
    return embed


def format_match_score(score: Dict[str, Any], match_type: str) -> str:
    """Format match score for display.
    
    Args:
        score: Score dictionary
        match_type: Type of match (singles/doubles)
        
    Returns:
        Formatted score string
    """
    if not score or 'sets' not in score:
        return "No score recorded"
    
    set_scores = []
    for i, set_data in enumerate(score['sets'], 1):
        games1 = set_data.get('player1_games', 0)
        games2 = set_data.get('player2_games', 0)
        set_scores.append(f"Set {i}: {games1}-{games2}")
    
    return "\n".join(set_scores) 