# src/cogs/user/commands/get_started/command.py
"""Implementation of the /get-started command with step-by-step profile setup."""

from nextcord import Interaction, Embed, Color
import logging
from datetime import datetime, timedelta, timezone
from typing import List
from decimal import Decimal
from .constants import (
    INTEREST_STEP, INTEREST_OPTIONS, SKILL_LEVEL_OPTIONS, GENDER_OPTIONS,
    SKILL_LEVEL_STEP, GENDER_STEP, LOCATION_STEP, PLAYER_GENDER_STEP,
    PLAYER_GENDER_OPTIONS, DOB_STEP
)
from .ntrp.knows_ntrp_step import knows_ntrp_step
from .ntrp.rating_select_step import ntrp_select_step
from .ntrp.questions_step import ntrp_questions_step
from .ntrp.rating_confirm_step import rating_confirm_step
from .player_gender_step import player_gender_step
from .dob_step import dob_step
from src.cogs.user.views import (
    show_skill_level_select,
    show_gender_select,
    show_location_select,
    show_interests_select
)
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.utils.role_manager import RoleManager
from src.utils.responses import Responses
from src.config.dynamodb_config import get_db

logger = logging.getLogger(__name__)


class ProfileSetup:
    """Manages the step-by-step profile setup process."""

    def __init__(self, interaction: Interaction):
        self.interaction = interaction
        self.player_dao = PlayerDAO(get_db())
        self.court_dao = CourtDAO(get_db())
        self.role_manager = RoleManager()
        self.knows_ntrp = None
        self.ntrp_rating = None
        self.rating_responses = None
        self.player_gender = None
        self.date_of_birth = None
        self.skill_level_preferences = None
        self.gender_preference = None
        self.selected_interests = None
        self.preferred_locations = None

    async def start(self):
        """Start the profile setup process."""
        try:
            # Start with NTRP knowledge question
            await knows_ntrp_step(self.interaction, self.handle_knows_ntrp)

        except Exception as e:
            logger.error(f"Error starting profile setup: {e}")
            await Responses.send_error(
                self.interaction,
                "Setup Failed",
                "An error occurred starting the setup. Please try again."
            )

    async def handle_knows_ntrp(self, interaction: Interaction, knows_ntrp: bool):
        """Handle whether user knows their NTRP rating."""
        try:
            self.knows_ntrp = knows_ntrp

            if knows_ntrp:
                # Show NTRP selection for users who know their rating
                await ntrp_select_step(interaction, self.handle_ntrp_selection)
            else:
                # Start questions flow for users who don't know their rating
                await ntrp_questions_step(interaction, self.handle_questions_complete)

        except Exception as e:
            logger.error(f"Error handling NTRP knowledge response: {e}")
            await Responses.send_error(
                interaction,
                "Setup Failed",
                "An error occurred. Please try again."
            )

    async def handle_ntrp_selection(self, interaction: Interaction, rating: float):
        """Handle direct NTRP rating selection."""
        try:
            # Convert float to Decimal for DynamoDB
            self.ntrp_rating = Decimal(str(rating))
            # Move to player gender selection
            await player_gender_step(interaction, self.handle_player_gender_submission)

        except Exception as e:
            logger.error(f"Error handling NTRP selection: {e}")
            await Responses.send_error(
                interaction,
                "Setup Failed",
                "An error occurred. Please try again."
            )

    async def handle_questions_complete(self, interaction: Interaction, calculated_rating: float, responses: dict):
        """Handle completion of NTRP questions."""
        try:
            self.rating_responses = responses
            # Show rating confirmation with calculated rating
            await rating_confirm_step(interaction, calculated_rating, self.handle_rating_confirmation)

        except Exception as e:
            logger.error(f"Error handling questions completion: {e}")
            await Responses.send_error(
                interaction,
                "Setup Failed",
                "An error occurred. Please try again."
            )

    async def handle_rating_confirmation(self, interaction: Interaction, confirmed_rating: float):
        """Handle confirmation of calculated NTRP rating."""
        try:
            # Convert float to Decimal for DynamoDB
            self.ntrp_rating = Decimal(str(confirmed_rating))
            # Move to player gender selection
            await player_gender_step(interaction, self.handle_player_gender_submission)

        except Exception as e:
            logger.error(f"Error handling rating confirmation: {e}")
            await Responses.send_error(
                interaction,
                "Setup Failed",
                "An error occurred. Please try again."
            )

    async def handle_player_gender_submission(self, interaction: Interaction, gender: str):
        """Handle player gender submission."""
        try:
            self.player_gender = gender
            # Move to date of birth selection
            await dob_step(interaction, self.handle_dob_submission)
        except Exception as e:
            logger.error(f"Error handling player gender submission: {e}")
            await Responses.send_error(
                interaction,
                "Setup Failed",
                "An error occurred. Please try again."
            )

    async def handle_dob_submission(self, interaction: Interaction, dob: str):
        """Handle date of birth submission."""
        try:
            self.date_of_birth = dob
            # Move to skill level preference
            await show_skill_level_select(
                interaction,
                self.handle_skill_level_submission,
                SKILL_LEVEL_STEP,
                button_label="Continue"  # Use "Continue" for the profile setup flow
            )
        except Exception as e:
            logger.error(f"Error handling date of birth submission: {e}")
            await Responses.send_error(
                interaction,
                "Setup Failed",
                "An error occurred. Please try again."
            )

    async def handle_skill_level_submission(self, interaction: Interaction, skill_levels: List[str]):
        """Handle skill level preference submission."""
        try:
            self.skill_level_preferences = skill_levels
            # Move to gender preference
            await show_gender_select(
                interaction,
                self.handle_gender_preference_submission,
                GENDER_STEP,
                pre_selected_preferences=None,  # No pre-selected preference for new users
                button_label="Continue"  # Use "Continue" for the profile setup flow
            )
        except Exception as e:
            logger.error(f"Error handling skill level submission: {e}")
            await Responses.send_error(
                interaction,
                "Setup Failed",
                "An error occurred. Please try again."
            )

    async def handle_gender_preference_submission(self, interaction: Interaction, gender_prefs: List[str]):
        """Handle gender preference submission."""
        try:
            self.gender_preference = gender_prefs
            # Move to interests selection
            await self.show_interests_step(interaction)
        except Exception as e:
            logger.error(f"Error handling gender preference submission: {e}")
            await Responses.send_error(
                interaction,
                "Setup Failed",
                "An error occurred. Please try again."
            )

    async def show_interests_step(self, interaction: Interaction):
        """Show interests selection step."""
        try:
            await show_interests_select(
                interaction,
                self.handle_interests_submission,
                INTEREST_STEP,
                INTEREST_OPTIONS,
                button_label="Continue"  # Use "Continue" for the profile setup flow
            )
        except Exception as e:
            logger.error(f"Error showing interests step: {e}")
            if interaction.response.is_done():
                await interaction.followup.send(
                    "An error occurred. Please try again.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "An error occurred. Please try again.",
                    ephemeral=True
                )

    async def handle_interests_submission(self, interaction: Interaction, interests: List[str]):
        """Handle interests submission and move to location selection."""
        try:
            self.selected_interests = interests
            
            # Get available court IDs and names from CourtDAO
            courts = self.court_dao.list_courts()
            
            if not courts:
                await Responses.send_error(
                    interaction,
                    "Setup Failed",
                    "No court locations are available at the moment."
                )
                return
            
            # Extract court IDs and names for the location selector
            locations = [(court.court_id, court.name) for court in courts]
            
            await show_location_select(
                interaction,
                locations,
                self.handle_locations_submission,
                LOCATION_STEP,
                button_label="Finish"  # Use "Finish" for the final step
            )
        except Exception as e:
            logger.error(f"Error handling interests submission: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Setup Failed",
                "An error occurred. Please try again."
            )

    async def handle_locations_submission(self, interaction: Interaction, locations: List[str]):
        """Handle location submission and complete profile setup."""
        try:
            self.preferred_locations = locations

            # Calculate calibration period end date (as ISO format string with UTC timezone)
            calibration_ends_at = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()

            # Structure preferences as a dictionary
            preferences = {
                "locations": self.preferred_locations,
                "skill_levels": self.skill_level_preferences,
                "gender": self.gender_preference
            }

            # Save to database using create_player
            self.player_dao.create_player(
                guild_id=interaction.guild.id,
                user_id=interaction.user.id,
                username=interaction.user.name,
                dob=self.date_of_birth,
                gender=self.player_gender,
                ntrp_rating=self.ntrp_rating,
                interests=self.selected_interests,
                knows_ntrp=self.knows_ntrp,
                preferences=preferences,
                rating_responses=self.rating_responses,
                calibration_ends_at=calibration_ends_at,
                last_rating_update=datetime.now(timezone.utc).isoformat()
            )
            success = True

            # Update role from visitor to member
            role_success = await self.role_manager.update_member_role(
                interaction.user,
                'visitor',
                'member'
            )
            
            # Assign skill level role based on NTRP rating
            skill_role_success = await self.role_manager.assign_skill_role(
                interaction.user,
                float(self.ntrp_rating)  # Convert Decimal back to float for role manager
            )

            # Get court names for display
            court_names = []
            for court_id in self.preferred_locations:
                court = self.court_dao.get_court(court_id)
                if court:
                    court_names.append(court.name)
                else:
                    court_names.append(court_id)  # Fallback to ID if court not found

            # Get labels for preferences
            skill_labels = [SKILL_LEVEL_OPTIONS[level]['label'] for level in self.skill_level_preferences]
            
            # Handle multiple gender preferences
            gender_labels = []
            for pref in self.gender_preference:
                if pref in GENDER_OPTIONS:
                    gender_labels.append(GENDER_OPTIONS[pref]['label'])
            gender_label_text = ", ".join(gender_labels) if gender_labels else "None"
            
            interest_labels = [INTEREST_OPTIONS[i]['label'] for i in self.selected_interests if i in INTEREST_OPTIONS]

            # Get player gender label
            player_gender_label = PLAYER_GENDER_OPTIONS[self.player_gender]['label'] if self.player_gender in PLAYER_GENDER_OPTIONS else self.player_gender

            # Create completion message
            description = (
                f"NTRP Rating: {float(self.ntrp_rating)}\n"
                f"Gender: {player_gender_label}\n"
                f"Date of Birth: {self.date_of_birth}\n"
                f"Skill Level Preferences: {', '.join(skill_labels)}\n"
                f"Gender Preference: {gender_label_text}\n"
                f"Interests: {', '.join(interest_labels)}\n"
                f"Preferred Locations: {', '.join(court_names)}\n\n"
                f"{'✅' if success else '❌'} Profile saved\n"
                f"{'✅' if role_success else '❌'} Club Member role assigned\n"
                f"{'✅' if skill_role_success else '❌'} Skill level role assigned\n\n"
                "Note: Your rating can be adjusted during the 2-week calibration period."
            )

            await Responses.send_success(
                interaction,
                "Profile Setup Complete!",
                description,
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error handling submission: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Setup Failed",
                "An error occurred saving your profile. Please try again."
            )


async def get_started_command(interaction: Interaction):
    """Handle the /get-started command."""
    try:
        # Initialize DAO
        player_dao = PlayerDAO(get_db())

        # Check if user already has a profile
        existing_player = player_dao.get_player(interaction.guild.id, interaction.user.id)

        if existing_player:
            await Responses.send_warning(
                interaction,
                "Profile Already Exists",
                "You have already set up your profile. Please use `/update-profile` to make any changes."
            )
            return

        # Proceed with profile setup if user doesn't exist
        setup = ProfileSetup(interaction)
        await setup.start()

    except Exception as e:
        logger.error(f"Error in get_started_command: {e}", exc_info=True)
        await Responses.send_error(
            interaction,
            "Command Failed",
            "An error occurred while processing your command. Please try again."
        )
