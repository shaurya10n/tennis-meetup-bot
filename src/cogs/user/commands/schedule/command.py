"""Implementation of schedule commands."""

import nextcord
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from src.config.dynamodb_config import get_db
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.models.dynamodb.schedule import Schedule
from src.utils.responses import Responses
from src.utils.matching_algorithm import TennisMatchingAlgorithm
from .constants import (
    ERRORS,
    SUCCESS,
    EMBEDS,
    TIME_PERIODS,
    CONFIRM_MESSAGES,
    HELP,
    DATE_FORMAT,
    TIME_FORMAT,
    AUTOMATIC_MATCHMAKING
)
from .parser.nlp_parser import TimeParser
from .views.schedule_view import ScheduleListView, ConfirmView
from src.cogs.user.views.schedule_preferences import show_schedule_preferences

logger = logging.getLogger(__name__)

class ScheduleCommands:
    """Handler for schedule-related commands."""

    def __init__(self):
        """Initialize command handler."""
        db = get_db()
        self.schedule_dao = ScheduleDAO(db)
        self.player_dao = PlayerDAO(db)
        self.time_parser = TimeParser()
        
        # Initialize matching algorithm for automatic matchmaking
        from src.database.dao.dynamodb.court_dao import CourtDAO
        from src.database.dao.dynamodb.match_dao import MatchDAO
        self.court_dao = CourtDAO(db)
        self.match_dao = MatchDAO(db)
        self.matching_algorithm = TennisMatchingAlgorithm(
            self.player_dao, self.schedule_dao, self.court_dao, self.match_dao
        )

    async def _check_profile_complete(
        self,
        interaction: nextcord.Interaction,
        embed_title: str
    ) -> bool:
        """Check if user's profile is complete.
        
        Args:
            interaction (nextcord.Interaction): Command interaction
            embed_title (str): Title for error embed

        Returns:
            bool: True if profile is complete, False otherwise
        """
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        
        player = self.player_dao.get_player(guild_id, user_id)
        if not player:
            await Responses.send_error(
                interaction,
                embed_title,
                ERRORS["INCOMPLETE_PROFILE"].format(missing_fields="- all profile information")
            )
            return False

        is_complete, missing_fields = player.is_profile_complete()
        if not is_complete:
            # Format missing fields as bullet points
            formatted_fields = "\n".join([f"- {field}" for field in missing_fields])
            await Responses.send_error(
                interaction,
                embed_title,
                ERRORS["INCOMPLETE_PROFILE"].format(missing_fields=formatted_fields)
            )
            return False

        return True
        
    def _extract_recurrence_info(self, time_description: str) -> Optional[Dict[str, Any]]:
        """Extract recurrence information from time description.
        
        Args:
            time_description (str): Time description string
            
        Returns:
            Optional[Dict[str, Any]]: Recurrence information or None if not recurring
        """
        try:
            # Use the TimeParser's internal method to extract recurrence pattern
            recurrence_info = self.time_parser._extract_recurrence_pattern(time_description)
            if not recurrence_info:
                return None
                
            recurrence_type, recurrence_value = recurrence_info
            
            # Create recurrence dictionary
            recurrence = {
                'type': recurrence_type,
            }
            
            # Add specific recurrence details
            if recurrence_type == 'weekly' and recurrence_value not in ['week']:
                recurrence['days'] = [recurrence_value]
            
            # Default recurrence end date (3 months from now)
            # Convert to timestamp for DynamoDB
            recurrence['until'] = int((datetime.now(self.time_parser.timezone) + timedelta(days=90)).timestamp())
            
            logger.info(f"Created recurrence pattern: {recurrence}")
            return recurrence
            
        except Exception as e:
            logger.error(f"Error extracting recurrence info: {e}", exc_info=True)
            return None

    async def _trigger_automatic_matchmaking(self, interaction: nextcord.Interaction, schedule: Schedule):
        """Trigger automatic matchmaking for a newly created schedule.
        
        Args:
            interaction: Discord interaction
            schedule: The newly created schedule
        """
        try:
            # Check if automatic matchmaking is enabled
            if not AUTOMATIC_MATCHMAKING["ENABLED"]:
                logger.info("Automatic matchmaking is disabled")
                return
            
            logger.info(f"Triggering automatic matchmaking for schedule {schedule.schedule_id}")
            
            # Find matches for this specific schedule
            suggestions = self.matching_algorithm.find_matches_for_schedule(
                str(interaction.guild.id), schedule.schedule_id
            )
            
            if not suggestions:
                logger.info(f"No match suggestions found for schedule {schedule.schedule_id}")
                # Send message to user that no matches were found
                await interaction.followup.send(
                    embed=nextcord.Embed(
                        title="🎾 No Matches Found",
                        description=(
                            "No suitable matches found for your new schedule.\n\n"
                            "This could be because:\n"
                            "• No other players are available during this time\n"
                            "• No players match your skill level or gender preferences\n"
                            "• No players prefer your preferred locations\n\n"
                            "Don't worry! Your schedule is still saved and other players can find you when they add their availability."
                        ),
                        color=nextcord.Color.orange()
                    ),
                    ephemeral=True
                )
                return
            
            # Filter out suggestions that already have matches and meet minimum score
            valid_suggestions = []
            for suggestion in suggestions:
                # Check if there's already a match for this suggestion
                existing_matches = self.match_dao.get_matches_by_players_and_time(
                    str(suggestion.guild_id),
                    [p.user_id for p in suggestion.players],
                    suggestion.suggested_time[0],
                    suggestion.suggested_time[1]
                )
                
                # Only include if no existing match and meets minimum score
                if not existing_matches and suggestion.overall_score >= AUTOMATIC_MATCHMAKING["MIN_SCORE"]:
                    valid_suggestions.append(suggestion)
            
            if not valid_suggestions:
                logger.info(f"No valid match suggestions found for schedule {schedule.schedule_id}")
                # Send message to user that no valid matches were found
                await interaction.followup.send(
                    embed=nextcord.Embed(
                        title="🎾 No Available Matches",
                        description=(
                            "No available matches found for your new schedule.\n\n"
                            "This could be because:\n"
                            "• All potential matches have already been scheduled\n"
                            "• Other players have pending match requests for this time\n"
                            "• Recent match requests were declined\n\n"
                            "Your schedule is still saved and will be available for future matchmaking!"
                        ),
                        color=nextcord.Color.blue()
                    ),
                    ephemeral=True
                )
                return
            
            # Sort by score and take the best matches
            valid_suggestions.sort(key=lambda x: x.overall_score, reverse=True)
            best_suggestions = valid_suggestions[:AUTOMATIC_MATCHMAKING["MAX_SUGGESTIONS"]]
            
            # Create match suggestions view
            from src.cogs.user.commands.find_match.views import MatchSuggestionView
            view = MatchSuggestionView(best_suggestions, self.match_dao, self.schedule_dao)
            
            # Create embed with match suggestions
            embed = self._create_automatic_matches_embed(best_suggestions, schedule)
            
            # Send the match suggestions
            await interaction.followup.send(
                embed=embed,
                view=view,
                ephemeral=True
            )
            
            logger.info(f"Sent {len(best_suggestions)} automatic match suggestions for schedule {schedule.schedule_id}")
            
        except Exception as e:
            logger.error(f"Error in automatic matchmaking: {e}", exc_info=True)
            # Don't fail the schedule creation if matchmaking fails
            pass
    
    def _create_automatic_matches_embed(self, suggestions, schedule):
        """Create an embed for automatic match suggestions."""
        import nextcord
        
        embed = nextcord.Embed(
            title="🎾 Automatic Match Suggestions",
            description=f"Found {len(suggestions)} potential matches for your new schedule!",
            color=nextcord.Color.blue()
        )
        
        for i, suggestion in enumerate(suggestions, 1):
            # Format players
            player_names = [p.username for p in suggestion.players]
            if suggestion.match_type == "singles":
                players_text = f"{player_names[0]} vs {player_names[1]}"
            else:
                players_text = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
            
            # Format time
            from datetime import datetime
            start_time = datetime.fromtimestamp(suggestion.suggested_time[0])
            end_time = datetime.fromtimestamp(suggestion.suggested_time[1])
            time_text = f"{start_time.strftime('%A, %B %d at %I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            
            # Format court
            court_text = suggestion.suggested_court.name if suggestion.suggested_court else "TBD"
            
            # Format score
            score_text = f"Match Score: {suggestion.overall_score:.1f}/1.0"
            
            # Format reasons
            reasons_text = ", ".join(suggestion.reasons[:2])  # Show top 2 reasons
            if len(suggestion.reasons) > 2:
                reasons_text += "..."
            
            field_value = (
                f"**{players_text}** ({suggestion.match_type.title()})\n"
                f"⏰ {time_text}\n"
                f"📍 {court_text}\n"
                f"📊 {score_text}\n"
                f"✨ {reasons_text}"
            )
            
            embed.add_field(
                name=f"Match {i}",
                value=field_value,
                inline=False
            )
        
        embed.set_footer(text="Click the buttons below to accept or decline matches")
        
        return embed

    async def add_schedule(
        self,
        interaction: nextcord.Interaction,
        time_description: str
    ):
        """Add a new schedule.
        
        Args:
            interaction (nextcord.Interaction): Command interaction
            time_description (str): Natural language time description
        """
        # Add interaction ID logging to track duplicate calls
        interaction_id = f"{interaction.id}_{interaction.user.id}_{time_description}"
        logger.info(f"add_schedule called with interaction_id: {interaction_id}")
        
        # Check profile completion first
        if not await self._check_profile_complete(interaction, EMBEDS["ADD_SCHEDULE"]):
            return
        try:
            guild_id = str(interaction.guild_id)
            user_id = str(interaction.user.id)
            
            logger.info(
                f"Adding schedule - User: {interaction.user.name} ({user_id}), "
                f"Guild: {interaction.guild.name} ({guild_id}), "
                f"Time: '{time_description}', Interaction ID: {interaction_id}"
            )

            # Parse time description
            start_time, end_time, error = self.time_parser.parse_time_description(
                time_description
            )
            if error:
                logger.warning(
                    f"Failed to parse time description '{time_description}': {error}"
                )
                # Use the specific error message from the parser
                error_message = f"❌ {error}\n\n{HELP['TIME_FORMAT']}"
                await Responses.send_error(
                    interaction,
                    EMBEDS["ADD_SCHEDULE"],
                    error_message
                )
                return

            # Extract recurrence pattern if present
            recurrence = self._extract_recurrence_info(time_description)

            
            # Convert datetime to timestamp for DynamoDB
            start_timestamp = int(start_time.timestamp())
            end_timestamp = int(end_time.timestamp())

            # Validate schedule times
            if start_time >= end_time:
                logger.warning("Invalid schedule: Start time must be before end time")
                await Responses.send_error(
                    interaction,
                    EMBEDS["ADD_SCHEDULE"],
                    "Start time must be before end time"
                )
                return

            if start_time < datetime.now(self.time_parser.timezone):
                logger.warning("Invalid schedule: Start time must be in the future")
                await Responses.send_error(
                    interaction,
                    EMBEDS["ADD_SCHEDULE"],
                    "Start time must be in the future"
                )
                return

            # Check for overlaps with the user's own schedules first
            user_overlapping_schedules = self.schedule_dao.get_overlapping_schedules(
                guild_id,
                start_timestamp, 
                end_timestamp,
                exclude_user_id=None  # Don't exclude user to check their own schedules
            )
            
            # Filter to only the current user's schedules
            user_overlapping_schedules = [s for s in user_overlapping_schedules if s.user_id == user_id]
            
            if user_overlapping_schedules:
                logger.warning(f"Schedule overlaps with {len(user_overlapping_schedules)} of user's own schedules")
                await Responses.send_error(
                    interaction,
                    EMBEDS["ADD_SCHEDULE"],
                    ERRORS["OVERLAPPING"]
                )
                return

            # Create and save schedule
            logger.info(f"Creating schedule - Guild: {guild_id}, User: {user_id}, Start: {start_timestamp}, End: {end_timestamp}, Interaction ID: {interaction_id}")
            schedule = self.schedule_dao.create_schedule(
                guild_id=guild_id,
                user_id=user_id,
                start_time=start_timestamp,
                end_time=end_timestamp,
                recurrence=recurrence,
                preference_overrides={},
                status="open"
            )
            logger.info(f"Created schedule with ID: {schedule.schedule_id}, Interaction ID: {interaction_id}")
            
            if not schedule:
                logger.error("Failed to save schedule")
                await Responses.send_error(
                    interaction,
                    EMBEDS["ADD_SCHEDULE"],
                    ERRORS["SAVE_FAILED"]
                )
                return

            # Format success message with schedule details
            date_str = start_time.strftime(DATE_FORMAT)
            start_time_str = start_time.strftime(TIME_FORMAT)
            end_time_str = end_time.strftime(TIME_FORMAT)
            recurrence_str = ""
            if recurrence:
                if recurrence['type'] == 'weekly' and 'days' in recurrence:
                    recurrence_str = f" (repeats every {recurrence['days'][0]})"
                else:
                    recurrence_str = f" (repeats {recurrence['type']})"

            # Send success message and show preferences view
            logger.info(
                f"Successfully added schedule for {interaction.user.name} "
                f"({start_time} - {end_time})"
            )
            
            # Respond to interaction immediately to prevent timeout
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title=EMBEDS["ADD_SCHEDULE"],
                    description=f"✅ Schedule created! Setting up preferences...",
                    color=nextcord.Color.blue()
                ),
                ephemeral=True
            )
            
            # Define callback for after preferences are set
            async def after_preferences(updated_schedule: Schedule):
                # Send final success message
                await interaction.followup.send(
                    embed=nextcord.Embed(
                        title=EMBEDS["ADD_SCHEDULE"],
                        description=SUCCESS["SCHEDULE_ADDED"].format(
                            date=date_str,
                            start_time=start_time_str,
                            end_time=end_time_str,
                            recurrence_str=recurrence_str
                        ),
                        color=nextcord.Color.green()
                    ),
                    ephemeral=True
                )
                
                # Trigger automatic matchmaking
                await self._trigger_automatic_matchmaking(interaction, updated_schedule)

            # Show preferences view using followup
            await show_schedule_preferences(interaction, schedule, after_preferences)

        except Exception as e:
            logger.error(f"Error adding schedule: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                EMBEDS["ADD_SCHEDULE"],
                ERRORS["GENERAL_ERROR"]
            )

    async def view_schedule(
        self,
        interaction: nextcord.Interaction,
        filter: Optional[str] = None
    ):
        """View schedules.
        
        Args:
            interaction (nextcord.Interaction): Command interaction
            filter (Optional[str]): Time period filter
        """
        # Check profile completion first
        if not await self._check_profile_complete(interaction, EMBEDS["VIEW_SCHEDULE"]):
            return
        try:
            guild_id = str(interaction.guild_id)
            user_id = str(interaction.user.id)
            
            logger.info(
                f"Viewing schedules - User: {interaction.user.name}, Filter: '{filter}'"
            )

            # Determine time range from filter
            start_after = None
            end_before = None

            if filter:
                filter = filter.lower()
                today = datetime.now(self.time_parser.timezone).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

                if filter == TIME_PERIODS["TODAY"]:
                    start_after = today
                    end_before = today + timedelta(days=1)
                elif filter == TIME_PERIODS["TOMORROW"]:
                    start_after = today + timedelta(days=1)
                    end_before = today + timedelta(days=2)
                elif filter == TIME_PERIODS["THIS_WEEK"]:
                    start_after = today
                    end_before = today + timedelta(days=7)
                elif filter == TIME_PERIODS["NEXT_WEEK"]:
                    start_after = today + timedelta(days=7)
                    end_before = today + timedelta(days=14)
                else:
                    logger.warning(f"Invalid filter: '{filter}'")
                    await Responses.send_error(
                        interaction,
                        EMBEDS["VIEW_SCHEDULE"],
                        f"{ERRORS['INVALID_FILTER']}\n\n{HELP['FILTER_FORMAT']}"
                    )
                    return

            # Convert to timestamps for DynamoDB
            start_timestamp = int(start_after.timestamp()) if start_after else None
            end_timestamp = int(end_before.timestamp()) if end_before else None

            # Get schedules (only for the current user)
            schedules = self.schedule_dao.get_user_schedules_in_time_range(
                guild_id,
                user_id=user_id,
                start_time=start_timestamp,
                end_time=end_timestamp
            ) if start_timestamp and end_timestamp else self.schedule_dao.get_user_schedules(guild_id, user_id=user_id)

            # Filter out cancelled schedules
            schedules = [s for s in schedules if s.status != "cancelled"]

            if not schedules:
                logger.info("No schedules found")
                await interaction.response.send_message(
                    "No schedules found for this period.",
                    ephemeral=True
                )
                return

            # Build user dictionary for display
            user_dict = {}
            for schedule in schedules:
                if schedule.user_id not in user_dict:
                    # Convert string user_id to int for Discord API
                    member = interaction.guild.get_member(int(schedule.user_id))
                    user_dict[schedule.user_id] = (
                        member.display_name if member else f"User {schedule.user_id}"
                    )

            # Create and send view
            logger.info(f"Displaying {len(schedules)} schedules")
            view = ScheduleListView(schedules, user_dict)
            await interaction.response.send_message(
                embed=await view.get_current_page_embed(),
                view=view,
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error viewing schedules: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                EMBEDS["VIEW_SCHEDULE"],
                ERRORS["GENERAL_ERROR"]
            )

    async def clear_schedule(
        self,
        interaction: nextcord.Interaction,
        period: str
    ):
        """Clear schedules for a period.
        
        Args:
            interaction (nextcord.Interaction): Command interaction
            period (str): Time period to clear
        """
        # Check profile completion first
        if not await self._check_profile_complete(interaction, EMBEDS["CLEAR_SCHEDULE"]):
            return
        try:
            guild_id = str(interaction.guild_id)
            user_id = str(interaction.user.id)
            
            logger.info(
                f"Clearing schedules - User: {interaction.user.name}, "
                f"Period: '{period}'"
            )

            # Determine time range from period
            period = period.lower()
            today = datetime.now(self.time_parser.timezone).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            if period == TIME_PERIODS["TODAY"]:
                start_after = today
                end_before = today + timedelta(days=1)
            elif period == TIME_PERIODS["TOMORROW"]:
                start_after = today + timedelta(days=1)
                end_before = today + timedelta(days=2)
            elif period == TIME_PERIODS["THIS_WEEK"]:
                start_after = today
                end_before = today + timedelta(days=7)
            elif period == TIME_PERIODS["NEXT_WEEK"]:
                start_after = today + timedelta(days=7)
                end_before = today + timedelta(days=14)
            else:
                logger.warning(f"Invalid period: '{period}'")
                await Responses.send_error(
                    interaction,
                    EMBEDS["CLEAR_SCHEDULE"],
                    f"{ERRORS['INVALID_FILTER']}\n\n{HELP['FILTER_FORMAT']}"
                )
                return

            # Convert to timestamps for DynamoDB
            start_timestamp = int(start_after.timestamp())
            end_timestamp = int(end_before.timestamp())

            # Create confirmation view
            async def confirm_callback(confirm_interaction: nextcord.Interaction):
                # Cancel schedules in the time range
                count = self.schedule_dao.cancel_user_schedules_in_time_range(
                    guild_id,
                    user_id=user_id,
                    start_time=start_timestamp,
                    end_time=end_timestamp
                )
                
                if count > 0:
                    logger.info(
                        f"Successfully cancelled {count} schedules for {interaction.user.name} "
                        f"({start_after} - {end_before})"
                    )
                    await confirm_interaction.response.edit_message(
                        content=SUCCESS["SCHEDULES_CLEARED"],
                        view=None
                    )
                else:
                    logger.info(f"No schedules found to clear for {interaction.user.name}")
                    await confirm_interaction.response.edit_message(
                        content="No schedules found to clear for this period.",
                        view=None
                    )

            view = ConfirmView(confirm_callback)
            await interaction.response.send_message(
                CONFIRM_MESSAGES["CLEAR_SCHEDULE"].format(period=period),
                view=view,
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error clearing schedules: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                EMBEDS["CLEAR_SCHEDULE"],
                ERRORS["GENERAL_ERROR"]
            )
