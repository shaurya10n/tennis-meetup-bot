"""Views for the find-matches command."""

import logging
from datetime import datetime
from typing import List, Optional
import nextcord
from nextcord import Interaction, Embed, Color, ButtonStyle
from nextcord.ui import View, Button

from src.database.dao.dynamodb.match_dao import MatchDAO
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.utils.matching_algorithm import MatchSuggestion
from src.utils.responses import Responses

logger = logging.getLogger(__name__)


class MatchSuggestionView(View):
    """View for displaying match suggestions with accept/decline buttons."""
    
    def __init__(self, suggestions: List[MatchSuggestion], match_dao: MatchDAO, schedule_dao: ScheduleDAO):
        """Initialize the view.
        
        Args:
            suggestions: List of match suggestions
            match_dao: Match data access object
            schedule_dao: Schedule data access object
        """
        super().__init__(timeout=300)  # 5 minute timeout
        self.suggestions = suggestions
        self.match_dao = match_dao
        self.schedule_dao = schedule_dao
        self.current_index = 0
        
        # Add navigation buttons (always visible)
        self.add_item(PreviousButton())
        self.add_item(NextButton())
        
        # Add action buttons (will be updated based on match status)
        self.add_item(AcceptMatchButton())
        self.add_item(NotInterestedButton())
        self.add_item(CancelInvitationButton())
        self.add_item(CancelMatchButton())
        self.add_item(ViewDetailsButton())
        
        # Initialize button states
        self.update_buttons()
    
    def get_current_suggestion(self) -> Optional[MatchSuggestion]:
        """Get the current suggestion being displayed."""
        if 0 <= self.current_index < len(self.suggestions):
            return self.suggestions[self.current_index]
        return None
    
    def get_current_match_status(self) -> Optional[str]:
        """Get the current match status from the database."""
        suggestion = self.get_current_suggestion()
        if not suggestion:
            return None
        
        # Check database state for current match status
        player_ids = [p.user_id for p in suggestion.players]
        matches = self.match_dao.get_matches_by_players(
            suggestion.guild_id, 
            player_ids
        )
        
        # Find the most recent match for this suggestion
        current_match = None
        if matches:
            # Filter matches that overlap with the suggestion time
            overlapping_matches = [
                m for m in matches 
                if m.start_time == suggestion.suggested_time[0] and m.end_time == suggestion.suggested_time[1]
            ]
            if overlapping_matches:
                current_match = max(overlapping_matches, key=lambda m: m.created_at)
        
        return current_match.status if current_match else None
    
    def update_buttons(self):
        """Update button states and visibility based on current index and match status."""
        # Remove all action buttons (but keep navigation and details buttons)
        action_types = (AcceptMatchButton, NotInterestedButton, CancelInvitationButton, CancelMatchButton)
        to_remove = [child for child in self.children if isinstance(child, action_types)]
        for child in to_remove:
            self.remove_item(child)

        suggestion = self.get_current_suggestion()
        if not suggestion:
            return

        # Check database state for current match status
        player_ids = [p.user_id for p in suggestion.players]
        matches = self.match_dao.get_matches_by_players(
            suggestion.guild_id, 
            player_ids
        )
        
        # Find the most recent match for this suggestion
        current_match = None
        if matches:
            # Filter matches that overlap with the suggestion time
            overlapping_matches = [
                m for m in matches 
                if m.start_time == suggestion.suggested_time[0] and m.end_time == suggestion.suggested_time[1]
            ]
            if overlapping_matches:
                current_match = max(overlapping_matches, key=lambda m: m.created_at)

        # Determine button state based on actual database state
        has_accepted_match = current_match and current_match.status == "scheduled"
        has_pending_request = current_match and current_match.status == "pending_confirmation"
        has_recently_declined = current_match and current_match.status == "cancelled"

        # Show Accept and Not Interested for new matches or recently declined matches
        if not (has_accepted_match or has_pending_request):
            self.add_item(AcceptMatchButton())
            self.add_item(NotInterestedButton())
        # Show Cancel Invitation for pending requests
        elif has_pending_request:
            self.add_item(CancelInvitationButton())
        # Show Cancel Match for accepted matches
        elif has_accepted_match:
            self.add_item(CancelMatchButton())

        # Navigation and details buttons
        for child in self.children:
            if isinstance(child, PreviousButton):
                child.disabled = self.current_index == 0
            elif isinstance(child, NextButton):
                child.disabled = self.current_index >= len(self.suggestions) - 1

    async def _send_confirmation_requests(self, interaction: Interaction, match, suggestion):
        """Send confirmation requests to other players via DM."""
        try:
            # Get the current user's ID
            current_user_id = str(interaction.user.id)
            
            # Find other players (excluding the current user)
            other_players = [p for p in suggestion.players if p.user_id != current_user_id]
            
            # Create confirmation embed
            start_time = datetime.fromtimestamp(suggestion.suggested_time[0])
            end_time = datetime.fromtimestamp(suggestion.suggested_time[1])
            time_text = f"{start_time.strftime('%A, %B %d at %I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            
            court_text = suggestion.suggested_court.name if suggestion.suggested_court else "TBD"
            
            # Get current user's name
            current_user = interaction.user.display_name or interaction.user.name
            
            confirmation_embed = Embed(
                title="🎾 Match Confirmation Request",
                description=f"**{current_user}** has requested to play a match with you!",
                color=Color.blue()
            )
            
            # Add match details
            player_names = [p.username for p in suggestion.players]
            if suggestion.match_type == "singles":
                players_text = f"{player_names[0]} vs {player_names[1]}"
            else:
                players_text = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
            
            confirmation_embed.add_field(
                name="Match Details",
                value=(
                    f"**Players:** {players_text}\n"
                    f"**Type:** {suggestion.match_type.title()}\n"
                    f"**Time:** {time_text}\n"
                    f"**Court:** {court_text}\n"
                    f"**Match ID:** {match.match_id}"
                ),
                inline=False
            )
            
            confirmation_embed.add_field(
                name="Action Required",
                value="Please confirm or decline this match request.",
                inline=False
            )
            
            # Send DM to each other player
            for player in other_players:
                try:
                    # Get Discord user object
                    discord_user = interaction.client.get_user(int(player.user_id))
                    if discord_user:
                        # Create confirmation view
                        confirmation_view = MatchConfirmationView(match.match_id, self.match_dao)
                        
                        # Send DM
                        await discord_user.send(embed=confirmation_embed, view=confirmation_view)
                        logger.info(f"Sent confirmation request to {player.username} ({player.user_id})")
                    else:
                        logger.warning(f"Could not find Discord user for {player.username} ({player.user_id})")
                except Exception as e:
                    logger.error(f"Failed to send DM to {player.username} ({player.user_id}): {e}")
            
            # Notify the current user
            await interaction.followup.send(
                f"✅ Match request sent! Waiting for confirmation from {len(other_players)} other player(s).",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error sending confirmation requests: {e}", exc_info=True)
            await interaction.followup.send(
                "⚠️ Match created but failed to send confirmation requests. Please contact the other players manually.",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error creating match: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Match Creation Failed",
                "An error occurred while creating the match. Please try again."
            )

    async def _notify_cancellation(self, interaction: Interaction, match, suggestion):
        """Notify all players about match cancellation."""
        try:
            # Create cancellation embed
            start_time = datetime.fromtimestamp(suggestion.suggested_time[0])
            end_time = datetime.fromtimestamp(suggestion.suggested_time[1])
            time_text = f"{start_time.strftime('%A, %B %d at %I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            
            court_text = suggestion.suggested_court.name if suggestion.suggested_court else "TBD"
            
            # Get cancelling user's name
            cancelling_user = interaction.user.display_name or interaction.user.name
            
            # Determine if this was an accepted match or pending request
            if match.status == "scheduled":
                title = "❌ Match Cancelled"
                description = f"**{cancelling_user}** has cancelled the scheduled match."
            else:  # pending_confirmation
                title = "❌ Match Request Cancelled"
                description = f"**{cancelling_user}** has cancelled the match request."
            
            cancellation_embed = Embed(
                title=title,
                description=description,
                color=Color.red()
            )
            
            # Add match details
            player_names = [p.username for p in suggestion.players]
            if suggestion.match_type == "singles":
                players_text = f"{player_names[0]} vs {player_names[1]}"
            else:
                players_text = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
            
            field_name = "Cancelled Match Details" if match.status == "scheduled" else "Cancelled Request Details"
            cancellation_embed.add_field(
                name=field_name,
                value=(
                    f"**Players:** {players_text}\n"
                    f"**Type:** {suggestion.match_type.title()}\n"
                    f"**Time:** {time_text}\n"
                    f"**Court:** {court_text}\n"
                    f"**Match ID:** {match.match_id}"
                ),
                inline=False
            )
            
            # Send notification to all players except the cancelling user
            cancelling_user_id = str(interaction.user.id)
            for player in suggestion.players:
                # Skip the cancelling user
                if player.user_id == cancelling_user_id:
                    continue
                try:
                    # Get Discord user object
                    discord_user = interaction.client.get_user(int(player.user_id))
                    if discord_user:
                        # Send DM
                        await discord_user.send(embed=cancellation_embed)
                        logger.info(f"Sent cancellation notification to {player.username} ({player.user_id})")
                    else:
                        logger.warning(f"Could not find Discord user for {player.username} ({player.user_id})")
                except Exception as e:
                    logger.error(f"Failed to send cancellation DM to {player.username} ({player.user_id}): {e}")
        except Exception as e:
            logger.error(f"Error sending cancellation notifications: {e}", exc_info=True)


class PreviousButton(Button):
    """Button to go to the previous match suggestion."""
    
    def __init__(self):
        super().__init__(
            label="◀️ Previous",
            style=ButtonStyle.secondary,
            custom_id="previous_match"
        )
    
    async def callback(self, interaction: Interaction):
        """Handle previous button click."""
        view = self.view
        if view.current_index > 0:
            view.current_index -= 1
            view.update_buttons()
            suggestion = view.get_current_suggestion()
            if suggestion:
                match_status = view.get_current_match_status()
                embed = create_suggestion_embed(suggestion, view.current_index + 1, len(view.suggestions), match_status)
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.response.send_message("Error: No suggestion found", ephemeral=True)
        else:
            await interaction.response.send_message("Already at the first match", ephemeral=True)


class NextButton(Button):
    """Button to go to the next match suggestion."""
    
    def __init__(self):
        super().__init__(
            label="Next ▶️",
            style=ButtonStyle.secondary,
            custom_id="next_match"
        )
    
    async def callback(self, interaction: Interaction):
        """Handle next button click."""
        view = self.view
        if view.current_index < len(view.suggestions) - 1:
            view.current_index += 1
            view.update_buttons()
            suggestion = view.get_current_suggestion()
            if suggestion:
                match_status = view.get_current_match_status()
                embed = create_suggestion_embed(suggestion, view.current_index + 1, len(view.suggestions), match_status)
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.response.send_message("Error: No suggestion found", ephemeral=True)
        else:
            await interaction.response.send_message("Already at the last match", ephemeral=True)


class AcceptMatchButton(Button):
    """Button to send a match invitation."""
    
    def __init__(self):
        super().__init__(
            label="📤 Send Invitation",
            style=ButtonStyle.success,
            custom_id="accept_match"
        )
    
    async def callback(self, interaction: Interaction):
        """Handle accept button click."""
        view = self.view
        suggestion = view.get_current_suggestion()
        
        if not suggestion:
            await interaction.response.send_message("Error: No suggestion found", ephemeral=True)
            return
        
        try:
            # Check if there's already a match request between these players
            player_ids = [p.user_id for p in suggestion.players]
            has_existing = view.match_dao.has_existing_match_request(
                str(interaction.guild.id), player_ids, 
                suggestion.suggested_time[0], suggestion.suggested_time[1]
            )
            
            if has_existing:
                await Responses.send_error(
                    interaction,
                    "Match Request Already Exists",
                    "A match request has already been sent to these players or was recently declined. Please wait before sending another request.",
                    ephemeral=True
                )
                return
            
            # Create the match with pending confirmation status
            match = view.match_dao.create_match(
                guild_id=str(interaction.guild.id),
                schedule_id=suggestion.schedules[0].schedule_id,  # Use first schedule as primary
                court_id=suggestion.suggested_court.court_id if suggestion.suggested_court else None,
                start_time=suggestion.suggested_time[0],
                end_time=suggestion.suggested_time[1],
                players=[p.user_id for p in suggestion.players],
                match_type=suggestion.match_type,
                status="pending_confirmation",
                player_ratings={p.user_id: p.ntrp_rating for p in suggestion.players}
            )
            
            # Update schedule statuses to indicate they're part of a match
            for schedule in suggestion.schedules:
                view.schedule_dao.update_schedule(
                    str(interaction.guild.id),
                    schedule.schedule_id,
                    match_id=match.match_id,
                    status="matched"
                )
            
            # Create pending confirmation embed
            embed = Embed(
                title="⏳ Match Pending Confirmation",
                description="Your match request has been sent! Waiting for other player(s) to confirm.",
                color=Color.orange()
            )
            
            # Add match details
            player_names = [p.username for p in suggestion.players]
            if suggestion.match_type == "singles":
                players_text = f"{player_names[0]} vs {player_names[1]}"
            else:
                players_text = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
            
            start_time = datetime.fromtimestamp(suggestion.suggested_time[0])
            end_time = datetime.fromtimestamp(suggestion.suggested_time[1])
            time_text = f"{start_time.strftime('%A, %B %d at %I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            
            court_text = suggestion.suggested_court.name if suggestion.suggested_court else "TBD"
            
            embed.add_field(
                name="Match Details",
                value=(
                    f"**Players:** {players_text}\n"
                    f"**Type:** {suggestion.match_type.title()}\n"
                    f"**Time:** {time_text}\n"
                    f"**Court:** {court_text}\n"
                    f"**Match ID:** {match.match_id}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="Status",
                value="⏳ Waiting for confirmation from other player(s)...",
                inline=False
            )
            
            # Update button states to reflect pending status
            view.update_buttons()
            
            await interaction.response.edit_message(embed=embed, view=view)
            
            # Send confirmation requests to other players
            await view._send_confirmation_requests(interaction, match, suggestion)
            
        except Exception as e:
            logger.error(f"Error creating match: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Match Creation Failed",
                "An error occurred while creating the match. Please try again."
            )
    
    async def _send_confirmation_requests(self, interaction: Interaction, match, suggestion):
        """Send confirmation requests to other players via DM."""
        try:
            # Get the current user's ID
            current_user_id = str(interaction.user.id)
            
            # Find other players (excluding the current user)
            other_players = [p for p in suggestion.players if p.user_id != current_user_id]
            
            # Create confirmation embed
            start_time = datetime.fromtimestamp(suggestion.suggested_time[0])
            end_time = datetime.fromtimestamp(suggestion.suggested_time[1])
            time_text = f"{start_time.strftime('%A, %B %d at %I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            
            court_text = suggestion.suggested_court.name if suggestion.suggested_court else "TBD"
            
            # Get current user's name
            current_user = interaction.user.display_name or interaction.user.name
            
            confirmation_embed = Embed(
                title="🎾 Match Confirmation Request",
                description=f"**{current_user}** has requested to play a match with you!",
                color=Color.blue()
            )
            
            # Add match details
            player_names = [p.username for p in suggestion.players]
            if suggestion.match_type == "singles":
                players_text = f"{player_names[0]} vs {player_names[1]}"
            else:
                players_text = f"{' vs '.join(player_names[:2])} vs {' vs '.join(player_names[2:])}"
            
            confirmation_embed.add_field(
                name="Match Details",
                value=(
                    f"**Players:** {players_text}\n"
                    f"**Type:** {suggestion.match_type.title()}\n"
                    f"**Time:** {time_text}\n"
                    f"**Court:** {court_text}\n"
                    f"**Match ID:** {match.match_id}"
                ),
                inline=False
            )
            
            confirmation_embed.add_field(
                name="Action Required",
                value="Please confirm or decline this match request.",
                inline=False
            )
            
            # Send DM to each other player
            for player in other_players:
                try:
                    # Get Discord user object
                    discord_user = interaction.client.get_user(int(player.user_id))
                    if discord_user:
                        # Create confirmation view
                        confirmation_view = MatchConfirmationView(match.match_id, self.match_dao)
                        
                        # Send DM
                        await discord_user.send(embed=confirmation_embed, view=confirmation_view)
                        logger.info(f"Sent confirmation request to {player.username} ({player.user_id})")
                    else:
                        logger.warning(f"Could not find Discord user for {player.username} ({player.user_id})")
                except Exception as e:
                    logger.error(f"Failed to send DM to {player.username} ({player.user_id}): {e}")
            
            # Notify the current user
            await interaction.followup.send(
                f"✅ Match request sent! Waiting for confirmation from {len(other_players)} other player(s).",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error sending confirmation requests: {e}", exc_info=True)
            await interaction.followup.send(
                "⚠️ Match created but failed to send confirmation requests. Please contact the other players manually.",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error creating match: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Match Creation Failed",
                "An error occurred while creating the match. Please try again."
            )


class NotInterestedButton(Button):
    """Button to indicate not interested in a match suggestion."""
    
    def __init__(self):
        super().__init__(
            label="😐 Not Interested",
            style=ButtonStyle.secondary,
            custom_id="not_interested"
        )
    
    async def callback(self, interaction: Interaction):
        """Handle not interested button click."""
        view = self.view
        suggestion = view.get_current_suggestion()
        
        if not suggestion:
            await interaction.response.send_message("Error: No suggestion found", ephemeral=True)
            return
        
        # Remove the not interested suggestion
        view.suggestions.pop(view.current_index)
        
        if not view.suggestions:
            # No more suggestions
            embed = Embed(
                title="😐 No More Matches",
                description="You've indicated you're not interested in all available matches. Try finding matches again later.",
                color=Color.orange()
            )
            
            # Disable all buttons
            for child in view.children:
                child.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            # Adjust index if needed
            if view.current_index >= len(view.suggestions):
                view.current_index = len(view.suggestions) - 1
            
            # Show next suggestion
            suggestion = view.get_current_suggestion()
            if suggestion:
                match_status = view.get_current_match_status()
                embed = create_suggestion_embed(suggestion, view.current_index + 1, len(view.suggestions), match_status)
                view.update_buttons()
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.response.send_message("Error: No suggestion found", ephemeral=True)


class CancelInvitationButton(Button):
    """Button to cancel a pending match invitation."""
    
    def __init__(self):
        super().__init__(
            label="❌ Cancel Invitation",
            style=ButtonStyle.danger,
            custom_id="cancel_invitation"
        )
    
    async def callback(self, interaction: Interaction):
        """Handle cancel invitation button click."""
        view = self.view
        suggestion = view.get_current_suggestion()
        
        if not suggestion:
            await interaction.response.send_message("Error: No suggestion found", ephemeral=True)
            return
        
        # Check database state for current match status
        player_ids = [p.user_id for p in suggestion.players]
        matches = view.match_dao.get_matches_by_players(
            suggestion.guild_id, player_ids
        )
        
        # Find the most recent match for this suggestion
        current_match = None
        if matches:
            # Filter matches that overlap with the suggestion time
            overlapping_matches = [
                m for m in matches 
                if m.start_time == suggestion.suggested_time[0] and m.end_time == suggestion.suggested_time[1]
            ]
            if overlapping_matches:
                current_match = max(overlapping_matches, key=lambda m: m.created_at)
        
        # Check if there's a pending request
        has_pending_request = current_match and current_match.status == "pending_confirmation"
        
        if not has_pending_request:
            await interaction.response.send_message("This invitation cannot be cancelled as it's not in a pending state.", ephemeral=True)
            return
        
        # Use the current match found above
        try:
            if not current_match:
                await interaction.response.send_message("Match not found in database.", ephemeral=True)
                return
            
            match = current_match
            
            # Cancel the match
            view.match_dao.update_match(
                str(interaction.guild.id),
                match.match_id,
                status="cancelled",
                cancelled_reason=f"Invitation cancelled by {interaction.user.display_name or interaction.user.name}"
            )
            
            # Reset schedule statuses
            for schedule in suggestion.schedules:
                view.schedule_dao.update_schedule(
                    str(interaction.guild.id),
                    schedule.schedule_id,
                    match_id=None,
                    status="open"
                )
            
            # Notify all players about the cancellation
            await view._notify_cancellation(interaction, match, suggestion)
            
            # Update the view to show the original suggestion again
            match_status = view.get_current_match_status()
            embed = create_suggestion_embed(suggestion, view.current_index + 1, len(view.suggestions), match_status)
            view.update_buttons()
            await interaction.response.edit_message(embed=embed, view=view)
            
            await interaction.followup.send("✅ Invitation has been cancelled and all players have been notified.", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error cancelling invitation: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Cancellation Failed",
                "An error occurred while cancelling the invitation. Please try again."
            )


class CancelMatchButton(Button):
    """Button to cancel an accepted match."""
    
    def __init__(self):
        super().__init__(
            label="❌ Cancel Match",
            style=ButtonStyle.danger,
            custom_id="cancel_match"
        )
    
    async def callback(self, interaction: Interaction):
        """Handle cancel button click."""
        view = self.view
        suggestion = view.get_current_suggestion()
        
        if not suggestion:
            await interaction.response.send_message("Error: No suggestion found", ephemeral=True)
            return
        
        # Check database state for current match status
        player_ids = [p.user_id for p in suggestion.players]
        matches = view.match_dao.get_matches_by_players(
            suggestion.guild_id, player_ids
        )
        
        # Find the most recent match for this suggestion
        current_match = None
        if matches:
            # Filter matches that overlap with the suggestion time
            overlapping_matches = [
                m for m in matches 
                if m.start_time == suggestion.suggested_time[0] and m.end_time == suggestion.suggested_time[1]
            ]
            if overlapping_matches:
                current_match = max(overlapping_matches, key=lambda m: m.created_at)
        
        # Check if there's an accepted match or pending request
        has_accepted_match = current_match and current_match.status == "scheduled"
        has_pending_request = current_match and current_match.status == "pending_confirmation"
        
        if not (has_accepted_match or has_pending_request):
            await interaction.response.send_message("This match cannot be cancelled as it hasn't been accepted or requested yet.", ephemeral=True)
            return
        
        try:
            if not current_match:
                await interaction.response.send_message("Match not found in database.", ephemeral=True)
                return
            
            match = current_match
            
            # Determine action type and success message
            if has_accepted_match:
                action_type = "cancelled"
                success_message = "Match has been cancelled and all players have been notified."
            else:  # has_pending_request
                action_type = "cancelled"
                success_message = "Match request has been cancelled and all players have been notified."
            
            # Cancel the match
            view.match_dao.update_match(
                str(interaction.guild.id),
                match.match_id,
                status="cancelled"
            )
            
            # Reset schedule statuses
            for schedule in suggestion.schedules:
                view.schedule_dao.update_schedule(
                    str(interaction.guild.id),
                    schedule.schedule_id,
                    match_id=None,
                    status="open"
                )
            
            # Notify all players about the cancellation
            await view._notify_cancellation(interaction, match, suggestion)
            
            # Update the view to reflect the cancellation and show normal UI
            view.update_buttons()
            match_status = view.get_current_match_status()
            embed = create_suggestion_embed(suggestion, view.current_index + 1, len(view.suggestions), match_status)
            
            await interaction.response.edit_message(embed=embed, view=view)
            await interaction.followup.send(success_message, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error cancelling match: {e}", exc_info=True)
            # Check if we've already responded
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"Error cancelling match: {str(e)}", 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"Error cancelling match: {str(e)}", 
                    ephemeral=True
                )


class ViewDetailsButton(Button):
    """Button to view detailed match information."""
    
    def __init__(self):
        super().__init__(
            label="📋 View Details",
            style=ButtonStyle.primary,
            custom_id="view_details"
        )
    
    async def callback(self, interaction: Interaction):
        """Handle view details button click."""
        view = self.view
        suggestion = view.get_current_suggestion()
        
        if not suggestion:
            await interaction.response.send_message("Error: No suggestion found", ephemeral=True)
            return
        
        # Create detailed embed
        embed = create_detailed_suggestion_embed(suggestion, view.current_index + 1, len(view.suggestions))
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


def create_suggestion_embed(suggestion: MatchSuggestion, current: int, total: int, match_status: str = None) -> Embed:
    """Create an embed for a single match suggestion."""
    # Use provided match status or fall back to checking reasons
    if match_status:
        if match_status == "scheduled":
            embed = Embed(
                title=f"✅ Match Accepted ({current}/{total})",
                description="This match has already been accepted and scheduled!",
                color=Color.green()
            )
        elif match_status == "pending_confirmation":
            embed = Embed(
                title=f"⏳ Match Pending ({current}/{total})",
                description="A match request has been sent and is waiting for confirmation.",
                color=Color.orange()
            )
        elif match_status == "cancelled":
            embed = Embed(
                title=f"❌ Recently Declined ({current}/{total})",
                description="A match request was recently declined by one of the players.",
                color=Color.red()
            )
        else:
            embed = Embed(
                title=f"🎾 Match Suggestion ({current}/{total})",
                description="Review this match suggestion and decide whether to accept or decline.",
                color=Color.blue()
            )
    else:
        # Fallback to checking reasons (for backward compatibility)
        has_accepted_match = any("✅ Match already accepted" in reason for reason in suggestion.reasons)
        has_pending_request = any("⏳ Match request pending" in reason for reason in suggestion.reasons)
        has_recently_declined = any("❌ Match request recently declined" in reason for reason in suggestion.reasons)
        
        if has_accepted_match:
            embed = Embed(
                title=f"✅ Match Accepted ({current}/{total})",
                description="This match has already been accepted and scheduled!",
                color=Color.green()
            )
        elif has_pending_request:
            embed = Embed(
                title=f"⏳ Match Pending ({current}/{total})",
                description="A match request has been sent and is waiting for confirmation.",
                color=Color.orange()
            )
        elif has_recently_declined:
            embed = Embed(
                title=f"❌ Recently Declined ({current}/{total})",
                description="A match request was recently declined by one of the players.",
                color=Color.red()
            )
        else:
            embed = Embed(
                title=f"🎾 Match Suggestion ({current}/{total})",
                description="Review this match suggestion and decide whether to accept or decline.",
                color=Color.blue()
            )
    
    # Player information
    player_names = [p.username for p in suggestion.players]
    if suggestion.match_type == "singles":
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
        value=suggestion.match_type.title(),
        inline=True
    )
    
    # Time
    start_time = datetime.fromtimestamp(suggestion.suggested_time[0])
    end_time = datetime.fromtimestamp(suggestion.suggested_time[1])
    time_text = f"{start_time.strftime('%A, %B %d')}\n{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
    
    embed.add_field(
        name="Time",
        value=time_text,
        inline=True
    )
    
    # Court
    court_text = suggestion.suggested_court.name if suggestion.suggested_court else "TBD"
    embed.add_field(
        name="Court",
        value=court_text,
        inline=True
    )
    
    # Compatibility score
    embed.add_field(
        name="Match Score",
        value=f"{suggestion.overall_score:.1f}/1.0",
        inline=True
    )
    
    # Top reasons
    reasons_text = ", ".join(suggestion.reasons[:3])
    if len(suggestion.reasons) > 3:
        reasons_text += "..."
    
    embed.add_field(
        name="Why This Match?",
        value=reasons_text,
        inline=False
    )
    
    return embed


def create_detailed_suggestion_embed(suggestion: MatchSuggestion, current: int, total: int) -> Embed:
    """Create a detailed embed with comprehensive match information."""
    embed = Embed(
        title=f"📋 Detailed Match Information ({current}/{total})",
        description="Comprehensive details about this match suggestion.",
        color=Color.blue()
    )
    
    # Player details
    for i, player in enumerate(suggestion.players, 1):
        player_info = (
            f"**NTRP Rating:** {float(player.ntrp_rating)}\n"
            f"**Gender:** {player.gender}\n"
            f"**Interests:** {', '.join(player.interests)}\n"
            f"**Preferred Locations:** {', '.join(player.preferences.get('locations', []))}\n"
            f"**Skill Preferences:** {', '.join(player.preferences.get('skill_levels', []))}\n"
            f"**Gender Preferences:** {', '.join(player.preferences.get('gender', []))}"
        )
        
        embed.add_field(
            name=f"Player {i}: {player.username}",
            value=player_info,
            inline=False
        )
    
    # Compatibility breakdown
    compat = suggestion.compatibility_details
    compatibility_info = (
        f"**NTRP Compatibility:** {compat.get('ntrp_compatibility', 0):.2f}\n"
        f"**Skill Preference Match:** {compat.get('skill_compatibility', 0):.2f}\n"
        f"**Gender Compatibility:** {compat.get('gender_compatibility', 0):.2f}\n"
        f"**Location Compatibility:** {compat.get('location_compatibility', 0):.2f}\n"
        f"**Time Overlap:** {compat.get('time_overlap', 0):.2f}\n"
        f"**Engagement Bonus:** {compat.get('engagement_bonus', 0):.2f}\n"
        f"**Match History:** {compat.get('match_history', 0):.2f}"
    )
    
    embed.add_field(
        name="Compatibility Breakdown",
        value=compatibility_info,
        inline=False
    )
    
    # Match details
    start_time = datetime.fromtimestamp(suggestion.suggested_time[0])
    end_time = datetime.fromtimestamp(suggestion.suggested_time[1])
    duration = (end_time - start_time).total_seconds() / 60
    
    match_info = (
        f"**Start Time:** {start_time.strftime('%A, %B %d at %I:%M %p')}\n"
        f"**End Time:** {end_time.strftime('%I:%M %p')}\n"
        f"**Duration:** {duration:.0f} minutes\n"
        f"**Court:** {suggestion.suggested_court.name if suggestion.suggested_court else 'TBD'}"
    )
    
    if suggestion.suggested_court:
        court_info = (
            f"**Location:** {suggestion.suggested_court.location}\n"
            f"**Surface:** {suggestion.suggested_court.surface_type}\n"
            f"**Indoor/Outdoor:** {'Indoor' if suggestion.suggested_court.is_indoor else 'Outdoor'}\n"
            f"**Amenities:** {', '.join(suggestion.suggested_court.amenities)}"
        )
        match_info += f"\n\n**Court Details:**\n{court_info}"
    
    embed.add_field(
        name="Match Details",
        value=match_info,
        inline=False
    )
    
    # All reasons
    embed.add_field(
        name="All Match Reasons",
        value="\n".join(f"• {reason}" for reason in suggestion.reasons),
        inline=False
    )
    
    return embed


class MatchConfirmationView(View):
    """View for confirming or declining a match request sent via DM."""
    
    def __init__(self, match_id: str, match_dao: MatchDAO):
        """Initialize the confirmation view.
        
        Args:
            match_id: ID of the match to confirm/decline
            match_dao: Match data access object
        """
        super().__init__(timeout=86400)  # 24 hour timeout
        self.match_id = match_id
        self.match_dao = match_dao
    
    @nextcord.ui.button(label="✅ Confirm Match", style=ButtonStyle.success, custom_id="confirm_match")
    async def confirm_match(self, button: Button, interaction: Interaction):
        """Handle match confirmation."""
        try:
            # Get the match
            match = self.match_dao.get_match_by_id(self.match_id)
            if not match:
                await interaction.response.send_message("❌ Match not found or already processed.", ephemeral=True)
                return
            
            if match.status != "pending_confirmation":
                if match.status == "cancelled":
                    await interaction.response.send_message("❌ This match invitation has been cancelled and is no longer valid.", ephemeral=True)
                    # Disable all buttons
                    for child in self.children:
                        child.disabled = True
                    await interaction.message.edit(view=self)
                else:
                    await interaction.response.send_message("❌ This match is no longer pending confirmation.", ephemeral=True)
                return
            
            # Update match status to scheduled
            updated_match = self.match_dao.update_match(
                str(match.guild_id),
                match.match_id,
                status="scheduled"
            )
            
            if not updated_match:
                await interaction.response.send_message("❌ Failed to confirm match. Please try again.", ephemeral=True)
                return
            
            # Create confirmation embed
            embed = Embed(
                title="✅ Match Confirmed!",
                description="The match has been confirmed and is now scheduled.",
                color=Color.green()
            )
            
            # Add match details
            start_time = datetime.fromtimestamp(match.start_time)
            end_time = datetime.fromtimestamp(match.end_time)
            time_text = f"{start_time.strftime('%A, %B %d at %I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            
            embed.add_field(
                name="Match Details",
                value=(
                    f"**Match ID:** {match.match_id}\n"
                    f"**Type:** {match.match_type.title()}\n"
                    f"**Time:** {time_text}\n"
                    f"**Players:** {len(match.players)} players"
                ),
                inline=False
            )
            
            embed.add_field(
                name="Next Steps",
                value=(
                    "• All players have been notified\n"
                    "• View your matches with `/matches-view type:upcoming` or `/matches-view type:completed`\n"
                    "• Update results after playing with `/complete-match`"
                ),
                inline=False
            )
            
            # Disable all buttons
            for child in self.children:
                child.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Notify all players about the confirmation
            await self._notify_all_players(interaction, match)
            
        except Exception as e:
            logger.error(f"Error confirming match: {e}", exc_info=True)
            await interaction.response.send_message("❌ An error occurred while confirming the match.", ephemeral=True)
    
    @nextcord.ui.button(label="😐 Not Interested", style=ButtonStyle.secondary, custom_id="not_interested")
    async def not_interested(self, button: Button, interaction: Interaction):
        """Handle match decline."""
        try:
            # Get the match
            match = self.match_dao.get_match_by_id(self.match_id)
            if not match:
                await interaction.response.send_message("❌ Match not found or already processed.", ephemeral=True)
                return
            
            if match.status != "pending_confirmation":
                if match.status == "cancelled":
                    await interaction.response.send_message("❌ This match invitation has been cancelled and is no longer valid.", ephemeral=True)
                    # Disable all buttons
                    for child in self.children:
                        child.disabled = True
                    await interaction.message.edit(view=self)
                else:
                    await interaction.response.send_message("❌ This match is no longer pending confirmation.", ephemeral=True)
                return
            
            # Update match status to cancelled
            updated_match = self.match_dao.update_match(
                str(match.guild_id),
                match.match_id,
                status="cancelled",
                cancelled_reason=f"Not interested - declined by {interaction.user.display_name or interaction.user.name}"
            )
            
            if not updated_match:
                await interaction.response.send_message("❌ Failed to decline match. Please try again.", ephemeral=True)
                return
            
            # Create decline embed
            embed = Embed(
                title="😐 Not Interested",
                description="You have indicated you're not interested in this match request.",
                color=Color.orange()
            )
            
            # Disable all buttons
            for child in self.children:
                child.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Notify other players about the decline
            await self._notify_decline(interaction, match)
            
        except Exception as e:
            logger.error(f"Error declining match: {e}", exc_info=True)
            await interaction.response.send_message("❌ An error occurred while declining the match.", ephemeral=True)
    
    async def _notify_all_players(self, interaction: Interaction, match):
        """Notify all players that the match has been confirmed."""
        try:
            # Create confirmation notification embed
            start_time = datetime.fromtimestamp(match.start_time)
            end_time = datetime.fromtimestamp(match.end_time)
            time_text = f"{start_time.strftime('%A, %B %d at %I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            
            notification_embed = Embed(
                title="🎾 Match Confirmed!",
                description="Your match has been confirmed and is now scheduled!",
                color=Color.green()
            )
            
            notification_embed.add_field(
                name="Match Details",
                value=(
                    f"**Match ID:** {match.match_id}\n"
                    f"**Type:** {match.match_type.title()}\n"
                    f"**Time:** {time_text}\n"
                    f"**Players:** {len(match.players)} players"
                ),
                inline=False
            )
            
            notification_embed.add_field(
                name="Next Steps",
                value=(
                    "• View your matches with `/matches-view type:upcoming` or `/matches-view type:completed`\n"
                    "• Update results after playing with `/complete-match`"
                ),
                inline=False
            )
            
            # Send DM to all players
            for player_id in match.players:
                try:
                    discord_user = interaction.client.get_user(int(player_id))
                    if discord_user:
                        await discord_user.send(embed=notification_embed)
                        logger.info(f"Sent confirmation notification to player {player_id}")
                except Exception as e:
                    logger.error(f"Failed to send confirmation notification to player {player_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error notifying players about confirmation: {e}", exc_info=True)
    
    async def _notify_decline(self, interaction: Interaction, match):
        """Notify other players that the match has been declined."""
        try:
            # Create decline notification embed
            decliner_name = interaction.user.display_name or interaction.user.name
            
            notification_embed = Embed(
                title="❌ Match Declined",
                description=f"**{decliner_name}** has declined the match request.",
                color=Color.red()
            )
            
            notification_embed.add_field(
                name="Match ID",
                value=match.match_id,
                inline=False
            )
            
            notification_embed.add_field(
                name="Next Steps",
                value="The match has been cancelled. You can find new matches using `/find-matches`.",
                inline=False
            )
            
            # Send DM to other players (excluding the one who declined)
            current_user_id = str(interaction.user.id)
            for player_id in match.players:
                if player_id != current_user_id:
                    try:
                        discord_user = interaction.client.get_user(int(player_id))
                        if discord_user:
                            await discord_user.send(embed=notification_embed)
                            logger.info(f"Sent decline notification to player {player_id}")
                    except Exception as e:
                        logger.error(f"Failed to send decline notification to player {player_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error notifying players about decline: {e}", exc_info=True) 