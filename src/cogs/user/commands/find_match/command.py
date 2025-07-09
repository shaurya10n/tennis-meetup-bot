"""Implementation of the /find-matches command."""

import logging
from datetime import datetime
from typing import Optional
import nextcord
from nextcord import Interaction, Embed, Color
from nextcord.ext import commands

from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.database.dao.dynamodb.match_dao import MatchDAO
from src.config.dynamodb_config import get_db
from src.utils.responses import Responses
from src.utils.matching_algorithm import TennisMatchingAlgorithm, MatchSuggestion
from .views import MatchSuggestionView

logger = logging.getLogger(__name__)


class FindMatchesCommand:
    """Handler for the find-matches command."""
    
    def __init__(self):
        """Initialize command handler."""
        db = get_db()
        self.player_dao = PlayerDAO(db)
        self.schedule_dao = ScheduleDAO(db)
        self.court_dao = CourtDAO(db)
        self.match_dao = MatchDAO(db)
        self.matching_algorithm = TennisMatchingAlgorithm(
            self.player_dao, self.schedule_dao, self.court_dao, self.match_dao
        )
    
    async def find_matches(self, interaction: Interaction, hours_ahead: Optional[int] = None):
        """Find potential matches for the user.
        
        Args:
            interaction: Discord interaction
            hours_ahead: Number of hours to look ahead (default: 168 = 1 week)
        """
        try:
            # Set default hours if not provided
            if hours_ahead is None:
                hours_ahead = 168  # 1 week
            
            # Validate hours_ahead
            if hours_ahead < 1 or hours_ahead > 720:  # Max 30 days
                await Responses.send_error(
                    interaction,
                    "Invalid Time Range",
                    "Please specify a time range between 1 hour and 30 days (720 hours)."
                )
                return
            
            # Check if user has a complete profile
            player = self.player_dao.get_player(str(interaction.guild.id), str(interaction.user.id))
            if not player:
                await Responses.send_error(
                    interaction,
                    "Profile Required",
                    "You need to complete your profile first. Use `/get-started` to set up your profile."
                )
                return
            
            # Check if profile is complete
            is_complete, missing_fields = player.is_profile_complete()
            if not is_complete:
                await Responses.send_error(
                    interaction,
                    "Incomplete Profile",
                    f"Please complete your profile first. Missing: {', '.join(missing_fields)}\n\nUse `/update-profile` to complete your profile."
                )
                return
            
            # Check if user has any schedules
            user_schedules = self.schedule_dao.get_user_schedules(
                str(interaction.guild.id), str(interaction.user.id)
            )
            if not user_schedules:
                await Responses.send_error(
                    interaction,
                    "No Schedules Found",
                    "You don't have any schedules set up. Use `/schedule add` to add your availability first."
                )
                return
            
            # Send initial response
            await interaction.response.send_message(
                embed=Embed(
                    title="🔍 Finding Matches",
                    description=f"Searching for matches in the next {hours_ahead} hours...",
                    color=Color.blue()
                ),
                ephemeral=True
            )
            
            # Find matches
            suggestions = self.matching_algorithm.find_matches_for_player(
                str(interaction.guild.id), str(interaction.user.id), hours_ahead
            )
            
            if not suggestions:
                await interaction.edit_original_message(
                    embed=Embed(
                        title="❌ No Matches Found",
                        description=(
                            f"No suitable matches found in the next {hours_ahead} hours.\n\n"
                            "This could be because:\n"
                            "• No other players are available during your scheduled times\n"
                            "• No players match your skill level or gender preferences\n"
                            "• No players prefer your preferred locations\n\n"
                            "Try:\n"
                            "• Adding more flexible schedules\n"
                            "• Updating your preferences in `/update-profile`\n"
                            "• Checking back later when more players are available"
                        ),
                        color=Color.orange()
                    )
                )
                return
            
            # Create match suggestions view
            view = MatchSuggestionView(suggestions, self.match_dao, self.schedule_dao)
            
            # Create embed with match suggestions
            embed = self._create_matches_embed(suggestions, hours_ahead)
            
            await interaction.edit_original_message(
                embed=embed,
                view=view
            )
            
        except Exception as e:
            logger.error(f"Error finding matches: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Match Finding Failed",
                "An error occurred while finding matches. Please try again."
            )
    
    async def find_matches_for_schedule(self, interaction: Interaction, schedule_id: str):
        """Find matches for a specific schedule.
        
        Args:
            interaction: Discord interaction
            schedule_id: Schedule ID to find matches for
        """
        try:
            # Check if user has a complete profile
            player = self.player_dao.get_player(str(interaction.guild.id), str(interaction.user.id))
            if not player:
                await Responses.send_error(
                    interaction,
                    "Profile Required",
                    "You need to complete your profile first. Use `/get-started` to set up your profile."
                )
                return
            
            # Check if the schedule belongs to the user
            schedule = self.schedule_dao.get_schedule(str(interaction.guild.id), schedule_id)
            if not schedule:
                await Responses.send_error(
                    interaction,
                    "Schedule Not Found",
                    "The specified schedule was not found."
                )
                return
            
            if schedule.user_id != str(interaction.user.id):
                await Responses.send_error(
                    interaction,
                    "Access Denied",
                    "You can only find matches for your own schedules."
                )
                return
            
            # Send initial response
            await interaction.response.send_message(
                embed=Embed(
                    title="🔍 Finding Matches",
                    description="Searching for matches for your schedule...",
                    color=Color.blue()
                ),
                ephemeral=True
            )
            
            # Find matches for the specific schedule
            suggestions = self.matching_algorithm.find_matches_for_schedule(
                str(interaction.guild.id), schedule_id
            )
            
            if not suggestions:
                await interaction.edit_original_message(
                    embed=Embed(
                        title="❌ No Matches Found",
                        description=(
                            "No suitable matches found for this schedule.\n\n"
                            "This could be because:\n"
                            "• No other players are available during this time\n"
                            "• No players match your skill level or gender preferences\n"
                            "• No players prefer your preferred locations\n\n"
                            "Try updating your schedule preferences or checking back later."
                        ),
                        color=Color.orange()
                    )
                )
                return
            
            # Create match suggestions view
            view = MatchSuggestionView(suggestions, self.match_dao, self.schedule_dao)
            
            # Create embed with match suggestions
            embed = self._create_matches_embed(suggestions, None, schedule)
            
            await interaction.edit_original_message(
                embed=embed,
                view=view
            )
            
        except Exception as e:
            logger.error(f"Error finding matches for schedule: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Match Finding Failed",
                "An error occurred while finding matches. Please try again."
            )
    
    def _create_matches_embed(self, suggestions: list[MatchSuggestion], 
                            hours_ahead: Optional[int], 
                            specific_schedule=None) -> Embed:
        """Create an embed showing match suggestions."""
        if specific_schedule:
            title = "🎾 Match Suggestions"
            description = f"Found {len(suggestions)} potential matches for your schedule:"
        else:
            title = "🎾 Match Suggestions"
            description = f"Found {len(suggestions)} potential matches in the next {hours_ahead} hours:"
        
        embed = Embed(title=title, description=description, color=Color.green())
        
        for i, suggestion in enumerate(suggestions[:5], 1):  # Show top 5
            # Check if there's an existing match for this suggestion
            match_status = self._get_match_status_for_suggestion(suggestion)
            
            # Format players
            player_names = [p.username for p in suggestion.players]
            if suggestion.match_type == "singles":
                players_text = f"{player_names[0]} vs {player_names[1]}"
            else:
                players_text = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
            
            # Format time
            start_time = datetime.fromtimestamp(suggestion.suggested_time[0])
            end_time = datetime.fromtimestamp(suggestion.suggested_time[1])
            time_text = f"{start_time.strftime('%A, %B %d at %I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            
            # Format court
            court_text = suggestion.suggested_court.name if suggestion.suggested_court else "TBD"
            
            # Format score
            score_text = f"Match Score: {suggestion.overall_score:.1f}/1.0"
            
            # Format reasons
            reasons_text = ", ".join(suggestion.reasons[:3])  # Show top 3 reasons
            if len(suggestion.reasons) > 3:
                reasons_text += "..."
            
            # Add status indicator if match exists
            status_text = ""
            if match_status == "scheduled":
                status_text = "\n✅ **Match Accepted**"
            elif match_status == "pending_confirmation":
                status_text = "\n⏳ **Match Pending Confirmation**"
            elif match_status == "cancelled":
                status_text = "\n❌ **Match Cancelled**"
            
            field_value = (
                f"**{players_text}** ({suggestion.match_type.title()})\n"
                f"⏰ {time_text}\n"
                f"📍 {court_text}\n"
                f"📊 {score_text}\n"
                f"✨ {reasons_text}{status_text}"
            )
            
            embed.add_field(
                name=f"Match {i}",
                value=field_value,
                inline=False
            )
        
        if len(suggestions) > 5:
            embed.add_field(
                name="More Matches",
                value=f"... and {len(suggestions) - 5} more matches available",
                inline=False
            )
        
        embed.set_footer(text="Click the buttons below to accept or decline matches")
        
        return embed
    
    def _get_match_status_for_suggestion(self, suggestion: MatchSuggestion) -> str:
        """Get the current match status for a suggestion by checking the database."""
        try:
            # Check if there's an existing match for these players and time
            existing_matches = self.match_dao.get_matches_by_players_and_time(
                str(suggestion.guild_id),
                [p.user_id for p in suggestion.players],
                suggestion.suggested_time[0],
                suggestion.suggested_time[1]
            )
            
            if existing_matches:
                # Return the status of the most recent match
                return existing_matches[0].status
            
            return None
        except Exception as e:
            logger.error(f"Error checking match status for suggestion: {e}")
            return None


# Command handler instance
find_matches_handler = FindMatchesCommand()


async def find_matches_command(interaction: Interaction, hours_ahead: Optional[int] = None):
    """Handle the /find-matches command."""
    await find_matches_handler.find_matches(interaction, hours_ahead)


async def find_matches_for_schedule_command(interaction: Interaction, schedule_id: str):
    """Handle finding matches for a specific schedule."""
    await find_matches_handler.find_matches_for_schedule(interaction, schedule_id) 