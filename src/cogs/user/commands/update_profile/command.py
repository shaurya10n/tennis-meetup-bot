# src/cogs/user/commands/update_profile/command.py
"""Implementation of the /update-profile command."""

import logging
from nextcord import Interaction, Embed, Color
from decimal import Decimal
from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.config.dynamodb_config import get_db
from src.utils.responses import Responses
from src.utils.role_manager import RoleManager
from datetime import datetime, timezone
from .views import UpdateOptionsView
from src.cogs.user.commands.get_started.constants import (
    INTEREST_OPTIONS, SKILL_LEVEL_OPTIONS, GENDER_OPTIONS
)
from ..get_started.ntrp.knows_ntrp_step import knows_ntrp_step
from ..get_started.ntrp.rating_select_step import ntrp_select_step
from ..get_started.ntrp.questions_step import ntrp_questions_step
from ..get_started.ntrp.rating_confirm_step import rating_confirm_step
from src.cogs.user.views import (
    show_location_select,
    show_skill_level_select,
    show_gender_select,
    show_interests_select
)
from .constants import UPDATE_MESSAGES

logger = logging.getLogger(__name__)


class ProfileUpdate:
    """Manages the profile update process."""

    def __init__(self, interaction: Interaction):
        self.interaction = interaction
        self.player_dao = PlayerDAO(get_db())
        self.court_dao = CourtDAO(get_db())
        self.role_manager = RoleManager()
        self.current_player = None

    async def start(self):
        """Start the profile update process."""
        try:
            # Get current profile
            self.current_player = self.player_dao.get_player(self.interaction.guild.id, self.interaction.user.id)

            if not self.current_player:
                await Responses.send_warning(
                    self.interaction,
                    "Profile Not Found",
                    "You haven't set up your profile yet. Use `/get-started` to create one."
                )
                return

            # Show current profile with update options
            embed = Embed(
                title="Update Profile",
                description=UPDATE_MESSAGES["select_option"],
                color=Color.blue()
            )

            view = UpdateOptionsView(self.handle_option_selection)
            await self.interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            logger.error(f"Error starting profile update: {e}", exc_info=True)
            await Responses.send_error(
                self.interaction,
                "Update Failed",
                "An error occurred while starting the update process. Please try again."
            )

    async def handle_option_selection(self, interaction: Interaction, option: str):
        """Handle update option selection."""
        try:
            if option == "ntrp":
                await self.start_ntrp_update(interaction)
            elif option == "skill_level":
                await self.show_skill_level_update(interaction)
            elif option == "gender":
                await self.show_gender_update(interaction)
            elif option == "locations":
                await self.start_location_update(interaction)
            elif option == "interests":
                await self.show_interests_update(interaction)
            else:
                logger.warning(f"Unknown update option selected: {option}")
                await Responses.send_error(interaction, "Invalid Option", "Please select a valid update option.")
        except Exception as e:
            logger.error(f"Error handling option selection: {e}", exc_info=True)
            await Responses.send_error(interaction, "Error", "Failed to process your selection.")

    async def show_skill_level_update(self, interaction: Interaction):
        """Show skill level preferences update interface."""
        try:
            # Get current preferences
            current_preferences = self.current_player.preferences.get("skill_levels", [])
            
            # Create a custom step config for the update view
            step_config = {
                "title": "Update Skill Level Preferences",
                "header": {
                    "emoji": "📊",
                    "title": "SKILL LEVEL PREFERENCES",
                    "separator": "———————————————"
                },
                "description": UPDATE_MESSAGES["current_skill_levels"].format(
                    "\n".join([
                        f"{SKILL_LEVEL_OPTIONS[pref]['emoji']} {SKILL_LEVEL_OPTIONS[pref]['label']}"
                        for pref in current_preferences if pref in SKILL_LEVEL_OPTIONS
                    ]) or "None"
                )
            }
            
            # Use the shared skill level select view
            await show_skill_level_select(
                interaction,
                self.handle_skill_level_update,
                step_config,
                pre_selected_levels=current_preferences
            )
        except Exception as e:
            logger.error(f"Error showing skill level update: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Error",
                "Failed to display skill level update interface."
            )

    async def handle_skill_level_update(self, interaction: Interaction, new_preferences: list):
        """Process skill level preferences update."""
        try:
            if set(new_preferences) == set(self.current_player.preferences.get("skill_levels", [])):
                await Responses.send_info(interaction, "No Change", "Your skill level preferences remain the same.")
                return

            # Update player's skill level preferences
            updated_preferences = {
                **self.current_player.preferences,
                "skill_levels": new_preferences
            }
            self.player_dao.update_player(
                self.interaction.guild.id,
                self.interaction.user.id,
                preferences=updated_preferences
            )
            success = True

            if success:
                preferences_text = "\n".join([
                    f"{SKILL_LEVEL_OPTIONS[pref]['emoji']} {SKILL_LEVEL_OPTIONS[pref]['label']}"
                    for pref in new_preferences
                ])
                await Responses.send_success(
                    interaction,
                    "Skill Level Preferences Updated",
                    f"Your skill level preferences have been updated to:\n{preferences_text}"
                )
            else:
                await Responses.send_error(
                    interaction,
                    "Update Failed",
                    "Failed to update your skill level preferences. Please try again."
                )

        except Exception as e:
            logger.error(f"Error updating skill level preferences: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Error",
                "An error occurred while updating your skill level preferences."
            )

    async def show_gender_update(self, interaction: Interaction):
        """Show gender preference update interface."""
        try:
            # Get current preference
            current_preference = self.current_player.preferences.get("gender", "none")
            
            # Log the raw value
            logger.info(f"Raw gender preference from database: {current_preference} (type: {type(current_preference).__name__})")
            
            # Handle the case where current_preference is a list
            if isinstance(current_preference, list):
                if not current_preference:
                    current_preference_text = "No preference set"
                else:
                    # Join the labels of all preferences
                    current_preference_text = ", ".join([
                        GENDER_OPTIONS[pref]['label']
                        for pref in current_preference if pref in GENDER_OPTIONS
                    ])
                    logger.info(f"Formatted list preference: {current_preference_text}")
            else:
                # Handle single gender preference (string)
                if current_preference in GENDER_OPTIONS:
                    current_preference_text = GENDER_OPTIONS[current_preference]['label']
                else:
                    current_preference_text = "No preference set"
                logger.info(f"Formatted string preference: {current_preference_text}")
            
            # Create a custom step config for the update view
            step_config = {
                "title": "Update Gender Preference",
                "header": {
                    "emoji": "👥",
                    "title": "GENDER PREFERENCE",
                    "separator": "———————————————"
                },
                "description": UPDATE_MESSAGES["current_gender"].format(current_preference_text)
            }
            
            # Use the shared gender select view
            await show_gender_select(
                interaction,
                self.handle_gender_update,
                step_config,
                pre_selected_preferences=current_preference
            )
        except Exception as e:
            logger.error(f"Error showing gender update: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Error",
                "Failed to display gender preference update interface."
            )

    async def handle_gender_update(self, interaction: Interaction, new_preferences: list):
        """Process gender preference update."""
        try:
            current_preference = self.current_player.preferences.get("gender", "none")
            
            # Add debug logging
            logger.info(f"Current gender preference: {current_preference}")
            logger.info(f"New gender preferences: {new_preferences}")
            
            # Convert current_preference to list for comparison if it's a string
            if isinstance(current_preference, str):
                current_preference = [current_preference]
            
            # Normalize both lists for comparison
            current_set = set(current_preference) if current_preference else set()
            new_set = set(new_preferences) if new_preferences else set()
            
            logger.info(f"Current set: {current_set}")
            logger.info(f"New set: {new_set}")
            
            if current_set == new_set:
                await Responses.send_info(interaction, "No Change", "Your gender preference remains the same.")
                return

            # Update player's gender preference
            updated_preferences = {
                **self.current_player.preferences,
                "gender": new_preferences
            }
            self.player_dao.update_player(
                self.interaction.guild.id,
                self.interaction.user.id,
                preferences=updated_preferences
            )
            success = True

            if success:
                # Format the preference text
                if len(new_preferences) == 1:
                    # Single preference
                    pref = new_preferences[0]
                    if pref in GENDER_OPTIONS:
                        preference_text = GENDER_OPTIONS[pref]['label']
                    else:
                        preference_text = "No preference"
                else:
                    # Multiple preferences
                    preference_text = ", ".join([
                        GENDER_OPTIONS[pref]['label']
                        for pref in new_preferences if pref in GENDER_OPTIONS
                    ])
                
                await Responses.send_success(
                    interaction,
                    "Gender Preference Updated",
                    f"Your gender preference has been updated to: {preference_text}"
                )
            else:
                await Responses.send_error(
                    interaction,
                    "Update Failed",
                    "Failed to update your gender preference. Please try again."
                )

        except Exception as e:
            logger.error(f"Error updating gender preference: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Error",
                "An error occurred while updating your gender preference."
            )

    async def start_ntrp_update(self, interaction: Interaction):
        """Start NTRP rating update process."""
        try:
            # Get current rating
            current_rating = self.current_player.ntrp_rating
            
            # Create custom title and description with current rating
            custom_title = "Update NTRP Rating"
            custom_description = (
                f"🎾 **NTRP RATING**\n"
                f"———————————————\n\n"
                f"Your current NTRP rating: **{float(current_rating)}**\n\n"
                f"Do you know your NTRP rating?\n\n"
                "• If you've played USTA leagues or tournaments, you likely have an NTRP rating.\n"
                "• If you're unsure, we'll ask a few questions to estimate your level.\n"
                "• Your rating can be adjusted during a 2-week calibration period."
            )
            
            # Start with NTRP knowledge question
            await knows_ntrp_step(interaction, self.handle_knows_ntrp, custom_title, custom_description)
        except Exception as e:
            logger.error(f"Error starting NTRP update: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Update Failed",
                "An error occurred while starting the NTRP update. Please try again."
            )

    async def handle_knows_ntrp(self, interaction: Interaction, knows_ntrp: bool):
        """Handle whether user knows their NTRP rating."""
        try:
            if knows_ntrp:
                await ntrp_select_step(interaction, self.handle_ntrp_selection)
            else:
                await ntrp_questions_step(interaction, self.handle_questions_complete)
        except Exception as e:
            logger.error(f"Error handling NTRP knowledge response: {e}")
            await Responses.send_error(
                interaction,
                "Update Failed",
                "An error occurred. Please try again."
            )

    async def handle_ntrp_selection(self, interaction: Interaction, rating: float):
        """Handle direct NTRP rating selection."""
        try:
            # Convert float to Decimal for DynamoDB
            decimal_rating = Decimal(str(rating))
            
            # Update player's NTRP rating
            self.player_dao.update_player(
                self.interaction.guild.id,
                self.interaction.user.id,
                ntrp_rating=decimal_rating,
                knows_ntrp=True,
                last_rating_update=datetime.now(timezone.utc).isoformat()
            )
            success = True

            # Assign appropriate skill level role based on the new rating
            skill_role_success = await self.role_manager.assign_skill_role(
                interaction.user,
                rating
            )

            if success:
                message = f"Your NTRP rating has been updated to: {rating}"
                if skill_role_success:
                    message += f"\nYour skill level role has been updated."
                message += f"\n{UPDATE_MESSAGES['rating_update_warning']}"
                
                await Responses.send_success(
                    interaction,
                    "NTRP Rating Updated",
                    message
                )
            else:
                await Responses.send_error(
                    interaction,
                    "Update Failed",
                    "Failed to update your NTRP rating. Please try again."
                )

        except Exception as e:
            logger.error(f"Error handling NTRP selection: {e}")
            await Responses.send_error(
                interaction,
                "Update Failed",
                "An error occurred. Please try again."
            )

    async def handle_questions_complete(self, interaction: Interaction, calculated_rating: float, responses: dict):
        """Handle completion of NTRP questions."""
        try:
            # Store responses in instance variable to access in callback
            self._temp_responses = responses
            await rating_confirm_step(interaction, calculated_rating, self.handle_rating_confirmation)
        except Exception as e:
            logger.error(f"Error handling questions completion: {e}")
            await Responses.send_error(
                interaction,
                "Update Failed",
                "An error occurred. Please try again."
            )

    async def handle_rating_confirmation(self, interaction: Interaction, confirmed_rating: float):
        """Handle confirmation of calculated NTRP rating."""
        try:
            # Convert float to Decimal for DynamoDB
            decimal_rating = Decimal(str(confirmed_rating))
            
            # Update player's NTRP rating and responses
            self.player_dao.update_player(
                self.interaction.guild.id,
                self.interaction.user.id,
                ntrp_rating=decimal_rating,
                rating_responses=getattr(self, '_temp_responses', None),
                knows_ntrp=False,
                last_rating_update=datetime.now(timezone.utc).isoformat()
            )
            success = True

            # Assign appropriate skill level role based on the new rating
            skill_role_success = await self.role_manager.assign_skill_role(
                interaction.user,
                confirmed_rating
            )

            if success:
                message = f"Your NTRP rating has been updated to: {confirmed_rating}"
                if skill_role_success:
                    message += f"\nYour skill level role has been updated."
                message += f"\n{UPDATE_MESSAGES['rating_update_warning']}"
                
                await Responses.send_success(
                    interaction,
                    "NTRP Rating Updated",
                    message
                )
            else:
                await Responses.send_error(
                    interaction,
                    "Update Failed",
                    "Failed to update your NTRP rating. Please try again."
                )

        except Exception as e:
            logger.error(f"Error handling rating confirmation: {e}")
            await Responses.send_error(
                interaction,
                "Update Failed",
                "An error occurred. Please try again."
            )

    async def start_location_update(self, interaction: Interaction):
        """Start location preferences update process."""
        try:
            # Get available court IDs and names from CourtDAO
            courts = self.court_dao.list_courts()
            
            if not courts:
                await Responses.send_error(
                    interaction,
                    "Update Failed",
                    "No court locations are available at the moment."
                )
                return
            
            # Extract court IDs and names for the location selector
            locations = [(court.court_id, court.name) for court in courts]
            
            # Get current location preferences
            current_locations = self.current_player.preferences.get("locations", [])
            
            # Create current locations text
            current_locations_text = ""
            for court_id in current_locations:
                court = self.court_dao.get_court(court_id)
                if court:
                    current_locations_text += f"🎾 {court.name}\n"
                else:
                    current_locations_text += f"🎾 {court_id}\n"
            
            # Create a custom step config for the update view
            step_config = {
                "title": "Update Locations",
                "header": {
                    "emoji": "📍",
                    "title": "LOCATIONS",
                    "separator": "———————————————"
                },
                "description": UPDATE_MESSAGES["current_locations"].format(current_locations_text or "None")
            }
            
            await show_location_select(
                interaction,
                locations,
                self.handle_locations_update,
                step_config,
                pre_selected_ids=current_locations
            )
        except Exception as e:
            logger.error(f"Error starting location update: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Update Failed",
                "An error occurred while starting the location update. Please try again."
            )

    async def handle_locations_update(self, interaction: Interaction, locations: list):
        """Handle location preferences update."""
        try:
            if set(locations) == set(self.current_player.preferences.get("locations", [])):
                await Responses.send_info(interaction, "No Change", "Your location preferences remain the same.")
                return

            # Update player's location preferences
            updated_preferences = {
                **self.current_player.preferences,
                "locations": locations
            }
            self.player_dao.update_player(
                self.interaction.guild.id,
                self.interaction.user.id,
                preferences=updated_preferences
            )
            success = True

            if success:
                # Get court names for display
                court_names = []
                for court_id in locations:
                    court = self.court_dao.get_court(court_id)
                    if court:
                        court_names.append(court.name)
                    else:
                        court_names.append(court_id)  # Fallback to ID if court not found
                
                locations_text = "\n".join([f"🎾 {name}" for name in court_names])
                await Responses.send_success(
                    interaction,
                    "Locations Updated",
                    f"Your preferred locations have been updated to:\n{locations_text}"
                )
            else:
                await Responses.send_error(
                    interaction,
                    "Update Failed",
                    "Failed to update your location preferences. Please try again."
                )

        except Exception as e:
            logger.error(f"Error updating locations: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Error",
                "An error occurred while updating your location preferences."
            )

    async def show_interests_update(self, interaction: Interaction):
        """Show interests update interface."""
        try:
            # Get current interests
            current_interests = self.current_player.interests
            
            # Create current interests text
            current_interests_text = "\n".join([
                f"{INTEREST_OPTIONS[i]['emoji']} {INTEREST_OPTIONS[i]['label']}"
                for i in current_interests if i in INTEREST_OPTIONS
            ])
            
            # Create a custom step config for the update view
            step_config = {
                "title": "Update Interests",
                "header": {
                    "emoji": "🎯",
                    "title": "INTERESTS",
                    "separator": "———————————————"
                },
                "description": UPDATE_MESSAGES["current_interests"].format(current_interests_text or "None")
            }
            
            # Use the shared interests select view
            await show_interests_select(
                interaction,
                self.handle_interests_update,
                step_config,
                INTEREST_OPTIONS,
                pre_selected_interests=current_interests
            )
            
            # Add debug logging
            logger.debug(f"Current player interests: {self.current_player.interests}")
        except Exception as e:
            logger.error(f"Error showing interests update: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Error",
                "Failed to display interests update interface."
            )

    async def handle_interests_update(self, interaction: Interaction, new_interests: list):
        """Process interests update."""
        try:
            if set(new_interests) == set(self.current_player.interests):
                await Responses.send_info(interaction, "No Change", "Your interests remain the same.")
                return

            # Validate interests before processing
            valid_interests = [i for i in new_interests if i in INTEREST_OPTIONS]

            if not valid_interests:
                await Responses.send_error(
                    interaction,
                    "Invalid Interests",
                    "The selected interests are not valid. Please try again."
                )
                return

            # Update player's interests
            self.player_dao.update_player(
                self.interaction.guild.id,
                self.interaction.user.id,
                interests=valid_interests
            )
            success = True

            if success:
                interests_text = "\n".join([
                    f"{INTEREST_OPTIONS[i]['emoji']} {INTEREST_OPTIONS[i]['label']}"
                    for i in valid_interests
                ])
                await Responses.send_success(
                    interaction,
                    "Interests Updated",
                    f"Your interests have been updated to:\n{interests_text}"
                )
                logger.info(f"Updated interests for user {self.interaction.user.id}: {valid_interests}")
            else:
                await Responses.send_error(
                    interaction,
                    "Update Failed",
                    "Failed to update your interests. Please try again."
                )

        except Exception as e:
            logger.error(f"Error updating interests: {e}", exc_info=True)
            logger.debug(f"New interests causing error: {new_interests}")
            await Responses.send_error(
                interaction,
                "Error",
                "An error occurred while updating your interests."
            )


async def update_profile_command(interaction: Interaction):
    """Handle the /update-profile command."""
    update = ProfileUpdate(interaction)
    await update.start()
