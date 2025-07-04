"""
Tennis Player Matching Algorithm

This module implements a sophisticated matching algorithm that considers:
- NTRP rating compatibility
- Skill level preferences
- Gender preferences
- Time availability
- Location preferences
- Match history and engagement
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from decimal import Decimal
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from src.database.dao.dynamodb.player_dao import PlayerDAO
from src.database.dao.dynamodb.schedule_dao import ScheduleDAO
from src.database.dao.dynamodb.court_dao import CourtDAO
from src.database.dao.dynamodb.match_dao import MatchDAO
from src.database.models.dynamodb.player import Player
from src.database.models.dynamodb.schedule import Schedule
from src.database.models.dynamodb.court import Court
from src.database.models.dynamodb.match import Match

logger = logging.getLogger(__name__)


@dataclass
class MatchCandidate:
    """Represents a potential match candidate."""
    player: Player
    schedule: Schedule
    compatibility_score: float
    ntrp_compatibility: float
    skill_preference_match: float
    gender_compatibility: float
    location_compatibility: float
    time_overlap: float
    engagement_bonus: float
    match_history_factor: float
    reasons: List[str]


@dataclass
class MatchSuggestion:
    """Represents a suggested match between players."""
    players: List[Player]
    schedules: List[Schedule]
    suggested_court: Optional[Court]
    suggested_time: Tuple[int, int]  # (start_time, end_time)
    overall_score: float
    match_type: str  # "singles" or "doubles"
    compatibility_details: Dict[str, float]
    reasons: List[str]


class TennisMatchingAlgorithm:
    """Advanced tennis player matching algorithm."""
    
    def __init__(self, player_dao: PlayerDAO, schedule_dao: ScheduleDAO, 
                 court_dao: CourtDAO, match_dao: MatchDAO):
        """Initialize the matching algorithm.
        
        Args:
            player_dao: Player data access object
            schedule_dao: Schedule data access object
            court_dao: Court data access object
            match_dao: Match data access object
        """
        self.player_dao = player_dao
        self.schedule_dao = schedule_dao
        self.court_dao = court_dao
        self.match_dao = match_dao
        self.timezone = ZoneInfo("America/Vancouver")
        
        # Configuration weights for different factors
        self.weights = {
            'ntrp_compatibility': 0.25,
            'skill_preference': 0.20,
            'gender_compatibility': 0.15,
            'location_compatibility': 0.15,
            'time_overlap': 0.15,
            'engagement_bonus': 0.05,
            'match_history': 0.05
        }
        
        # NTRP compatibility thresholds
        self.ntrp_thresholds = {
            'excellent': 0.5,  # Within 0.5 rating
            'good': 1.0,       # Within 1.0 rating
            'acceptable': 1.5,  # Within 1.5 rating
            'poor': 2.0        # Within 2.0 rating
        }
        
        # Skill level preference mappings
        self.skill_level_ranges = {
            'similar': 0.5,    # ±0.5 NTRP
            'above': 1.0,      # +1.0 NTRP
            'below': 1.0,      # -1.0 NTRP
            'any': 2.0         # Any level
        }
    
    def find_matches_for_player(self, guild_id: str, user_id: str, 
                               hours_ahead: int = 168) -> List[MatchSuggestion]:
        """Find potential matches for a specific player.
        
        Args:
            guild_id: Discord server ID
            user_id: Discord user ID
            hours_ahead: Number of hours to look ahead (default: 1 week)
            
        Returns:
            List[MatchSuggestion]: List of potential matches
        """
        try:
            # Get the player
            player = self.player_dao.get_player(guild_id, user_id)
            if not player:
                logger.warning(f"Player {user_id} not found in guild {guild_id}")
                return []
            
            # Get player's schedules
            player_schedules = self.schedule_dao.get_user_schedules(guild_id, user_id)
            if not player_schedules:
                logger.info(f"No schedules found for player {user_id}")
                return []
            
            # Get all available schedules in the time range
            now = int(datetime.now(self.timezone).timestamp())
            end_time = now + (hours_ahead * 3600)
            
            available_schedules = self.schedule_dao.get_overlapping_schedules(
                guild_id, now, end_time, exclude_user_id=user_id
            )
            
            if not available_schedules:
                logger.info("No other players available in the time range")
                return []
            
            # Get all players for the available schedules
            all_players = self._get_players_for_schedules(guild_id, available_schedules)
            
            # Find matches for each of the player's schedules
            all_suggestions = []
            
            for player_schedule in player_schedules:
                suggestions = self._find_matches_for_schedule(
                    player, player_schedule, available_schedules, all_players
                )
                all_suggestions.extend(suggestions)
            
            # Sort by overall score and return top suggestions
            all_suggestions.sort(key=lambda x: x.overall_score, reverse=True)
            return all_suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Error finding matches for player {user_id}: {e}")
            return []
    
    def find_matches_for_schedule(self, guild_id: str, schedule_id: str) -> List[MatchSuggestion]:
        """Find potential matches for a specific schedule.
        
        Args:
            guild_id: Discord server ID
            schedule_id: Schedule ID
            
        Returns:
            List[MatchSuggestion]: List of potential matches
        """
        try:
            # Get the schedule
            schedule = self.schedule_dao.get_schedule(guild_id, schedule_id)
            if not schedule:
                logger.warning(f"Schedule {schedule_id} not found")
                return []
            
            # Get the player
            player = self.player_dao.get_player(guild_id, schedule.user_id)
            if not player:
                logger.warning(f"Player {schedule.user_id} not found")
                return []
            
            # Get overlapping schedules
            overlapping_schedules = self.schedule_dao.get_overlapping_schedules(
                guild_id, schedule.start_time, schedule.end_time, 
                exclude_user_id=schedule.user_id
            )
            
            if not overlapping_schedules:
                logger.info("No overlapping schedules found")
                return []
            
            # Get all players for the overlapping schedules
            all_players = self._get_players_for_schedules(guild_id, overlapping_schedules)
            
            # Find matches
            suggestions = self._find_matches_for_schedule(
                player, schedule, overlapping_schedules, all_players
            )
            
            # Sort by overall score
            suggestions.sort(key=lambda x: x.overall_score, reverse=True)
            return suggestions[:10]
            
        except Exception as e:
            logger.error(f"Error finding matches for schedule {schedule_id}: {e}")
            return []
    
    def _find_matches_for_schedule(self, player: Player, player_schedule: Schedule,
                                  available_schedules: List[Schedule], 
                                  all_players: Dict[str, Player]) -> List[MatchSuggestion]:
        """Find matches for a specific schedule."""
        suggestions = []
        
        # Group schedules by time overlap
        overlapping_groups = self._group_schedules_by_overlap(player_schedule, available_schedules)
        
        for group in overlapping_groups:
            # Find singles matches (2 players)
            singles_suggestions = self._find_singles_matches(
                player, player_schedule, group, all_players
            )
            suggestions.extend(singles_suggestions)
            
            # Find doubles matches (4 players) if we have enough players
            if len(group) >= 3:  # Need at least 3 other players
                doubles_suggestions = self._find_doubles_matches(
                    player, player_schedule, group, all_players
                )
                suggestions.extend(doubles_suggestions)
        
        return suggestions
    
    def _find_singles_matches(self, player: Player, player_schedule: Schedule,
                             schedules: List[Schedule], 
                             all_players: Dict[str, Player]) -> List[MatchSuggestion]:
        """Find singles matches (2 players)."""
        suggestions = []
        
        for schedule in schedules:
            if schedule.user_id == player.user_id:
                continue
            
            other_player = all_players.get(schedule.user_id)
            if not other_player:
                continue
            
            # Calculate compatibility
            compatibility = self._calculate_compatibility(player, other_player, 
                                                        player_schedule, schedule)
            
            if compatibility['overall_score'] > 0.3:  # Minimum threshold
                # Find best court
                suggested_court = self._find_best_court(player, other_player, 
                                                      player_schedule, schedule)
                
                # Determine match time
                match_start, match_end = self._find_optimal_match_time(
                    player_schedule, schedule
                )
                
                # Check if there's already a match request between these players
                player_ids = [player.user_id, other_player.user_id]
                existing_status = self.match_dao.get_existing_match_status(
                    player.guild_id, player_ids, match_start, match_end
                )
                
                if existing_status:
                    if existing_status == "scheduled":
                        # Match has been accepted
                        compatibility['reasons'].append("✅ Match already accepted and scheduled")
                        # Keep the score but mark as accepted
                        compatibility['overall_score'] *= 0.8
                    elif existing_status == "pending_confirmation":
                        # Match request is pending
                        compatibility['reasons'].append("⏳ Match request pending confirmation")
                        # Reduce the score to make it less attractive
                        compatibility['overall_score'] *= 0.5
                    elif existing_status == "recently_cancelled":
                        # Match was recently declined
                        compatibility['reasons'].append("❌ Match request recently declined")
                        # Reduce the score significantly
                        compatibility['overall_score'] *= 0.3
                
                suggestion = MatchSuggestion(
                    players=[player, other_player],
                    schedules=[player_schedule, schedule],
                    suggested_court=suggested_court,
                    suggested_time=(match_start, match_end),
                    overall_score=compatibility['overall_score'],
                    match_type="singles",
                    compatibility_details=compatibility,
                    reasons=compatibility['reasons']
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _find_doubles_matches(self, player: Player, player_schedule: Schedule,
                             schedules: List[Schedule], 
                             all_players: Dict[str, Player]) -> List[MatchSuggestion]:
        """Find doubles matches (4 players)."""
        suggestions = []
        
        # Get all possible combinations of 3 other players
        other_schedules = [s for s in schedules if s.user_id != player.user_id]
        
        if len(other_schedules) < 3:
            return suggestions
        
        # Simple approach: take the first 3 compatible players
        # In a production system, you might want to try different combinations
        selected_schedules = other_schedules[:3]
        selected_players = []
        
        for schedule in selected_schedules:
            other_player = all_players.get(schedule.user_id)
            if other_player:
                selected_players.append(other_player)
        
        if len(selected_players) < 3:
            return suggestions
        
        # Calculate overall compatibility for the group
        compatibility = self._calculate_group_compatibility(
            [player] + selected_players, [player_schedule] + selected_schedules
        )
        
        if compatibility['overall_score'] > 0.25:  # Lower threshold for doubles
            # Find best court
            suggested_court = self._find_best_court_for_group(
                [player] + selected_players, [player_schedule] + selected_schedules
            )
            
            # Determine match time
            all_schedules = [player_schedule] + selected_schedules
            match_start, match_end = self._find_optimal_group_match_time(all_schedules)
            
            suggestion = MatchSuggestion(
                players=[player] + selected_players,
                schedules=[player_schedule] + selected_schedules,
                suggested_court=suggested_court,
                suggested_time=(match_start, match_end),
                overall_score=compatibility['overall_score'],
                match_type="doubles",
                compatibility_details=compatibility,
                reasons=compatibility['reasons']
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _calculate_compatibility(self, player1: Player, player2: Player,
                               schedule1: Schedule, schedule2: Schedule) -> Dict[str, Any]:
        """Calculate compatibility between two players."""
        reasons = []
        
        # NTRP compatibility
        ntrp_diff = abs(float(player1.ntrp_rating) - float(player2.ntrp_rating))
        ntrp_compatibility = self._calculate_ntrp_compatibility(ntrp_diff)
        
        # Skill preference compatibility
        skill_compatibility = self._calculate_skill_preference_compatibility(
            player1, player2
        )
        
        # Gender compatibility
        gender_compatibility = self._calculate_gender_compatibility(player1, player2)
        
        # Location compatibility
        location_compatibility = self._calculate_location_compatibility(
            player1, player2, schedule1, schedule2
        )
        
        # Time overlap
        time_overlap = self._calculate_time_overlap(schedule1, schedule2)
        
        # Engagement bonus
        engagement_bonus = self._calculate_engagement_bonus(player1, player2)
        
        # Match history factor
        match_history = self._calculate_match_history_factor(player1, player2)
        
        # Calculate overall score
        overall_score = (
            self.weights['ntrp_compatibility'] * ntrp_compatibility +
            self.weights['skill_preference'] * skill_compatibility +
            self.weights['gender_compatibility'] * gender_compatibility +
            self.weights['location_compatibility'] * location_compatibility +
            self.weights['time_overlap'] * time_overlap +
            self.weights['engagement_bonus'] * engagement_bonus +
            self.weights['match_history'] * match_history
        )
        
        # Add reasons
        if ntrp_compatibility > 0.8:
            reasons.append("Excellent skill level match")
        elif ntrp_compatibility > 0.6:
            reasons.append("Good skill level match")
        
        if skill_compatibility > 0.8:
            reasons.append("Matches skill preferences")
        
        if gender_compatibility > 0.8:
            reasons.append("Matches gender preferences")
        
        if location_compatibility > 0.8:
            reasons.append("Same preferred location")
        
        if time_overlap > 0.9:
            reasons.append("Perfect time overlap")
        
        if engagement_bonus > 0.5:
            reasons.append("High engagement players")
        
        if match_history > 0.5:
            reasons.append("Previous match history")
        
        return {
            'overall_score': overall_score,
            'ntrp_compatibility': ntrp_compatibility,
            'skill_compatibility': skill_compatibility,
            'gender_compatibility': gender_compatibility,
            'location_compatibility': location_compatibility,
            'time_overlap': time_overlap,
            'engagement_bonus': engagement_bonus,
            'match_history': match_history,
            'reasons': reasons
        }
    
    def _calculate_ntrp_compatibility(self, ntrp_diff: float) -> float:
        """Calculate NTRP compatibility score."""
        if ntrp_diff <= self.ntrp_thresholds['excellent']:
            return 1.0
        elif ntrp_diff <= self.ntrp_thresholds['good']:
            return 0.8
        elif ntrp_diff <= self.ntrp_thresholds['acceptable']:
            return 0.6
        elif ntrp_diff <= self.ntrp_thresholds['poor']:
            return 0.3
        else:
            return 0.0
    
    def _calculate_skill_preference_compatibility(self, player1: Player, player2: Player) -> float:
        """Calculate skill preference compatibility."""
        score = 0.0
        ntrp_diff = abs(float(player1.ntrp_rating) - float(player2.ntrp_rating))
        
        # Check player1's preferences
        player1_prefs = player1.preferences.get('skill_levels', [])
        if 'any' in player1_prefs:
            score += 0.5
        elif 'similar' in player1_prefs and ntrp_diff <= 0.5:
            score += 1.0
        elif 'above' in player1_prefs and float(player2.ntrp_rating) > float(player1.ntrp_rating):
            score += 1.0
        elif 'below' in player1_prefs and float(player2.ntrp_rating) < float(player1.ntrp_rating):
            score += 1.0
        
        # Check player2's preferences
        player2_prefs = player2.preferences.get('skill_levels', [])
        if 'any' in player2_prefs:
            score += 0.5
        elif 'similar' in player2_prefs and ntrp_diff <= 0.5:
            score += 1.0
        elif 'above' in player2_prefs and float(player1.ntrp_rating) > float(player2.ntrp_rating):
            score += 1.0
        elif 'below' in player2_prefs and float(player1.ntrp_rating) < float(player2.ntrp_rating):
            score += 1.0
        
        return score / 2.0  # Average of both players' preferences
    
    def _calculate_gender_compatibility(self, player1: Player, player2: Player) -> float:
        """Calculate gender compatibility."""
        player1_gender = player1.gender
        player2_gender = player2.gender
        
        # Get gender preferences
        player1_prefs = player1.preferences.get('gender', [])
        player2_prefs = player2.preferences.get('gender', [])
        
        # If either player has no preference, it's compatible
        if 'none' in player1_prefs or 'none' in player2_prefs:
            return 1.0
        
        # Check if preferences match
        if player1_gender in player2_prefs and player2_gender in player1_prefs:
            return 1.0
        
        # Partial match
        if player1_gender in player2_prefs or player2_gender in player1_prefs:
            return 0.5
        
        return 0.0
    
    def _calculate_location_compatibility(self, player1: Player, player2: Player,
                                        schedule1: Schedule, schedule2: Schedule) -> float:
        """Calculate location compatibility."""
        # Get preferred locations
        player1_locations = player1.preferences.get('locations', [])
        player2_locations = player2.preferences.get('locations', [])
        
        # Check for overlap
        common_locations = set(player1_locations) & set(player2_locations)
        if common_locations:
            return 1.0
        
        # Check if either player has no location preference
        if not player1_locations or not player2_locations:
            return 0.5
        
        return 0.0
    
    def _calculate_time_overlap(self, schedule1: Schedule, schedule2: Schedule) -> float:
        """Calculate time overlap between schedules."""
        overlap_start = max(schedule1.start_time, schedule2.start_time)
        overlap_end = min(schedule1.end_time, schedule2.end_time)
        
        if overlap_start >= overlap_end:
            return 0.0
        
        overlap_duration = overlap_end - overlap_start
        schedule1_duration = schedule1.end_time - schedule1.start_time
        schedule2_duration = schedule2.end_time - schedule2.start_time
        
        # Return the percentage of overlap relative to the shorter schedule
        min_duration = min(schedule1_duration, schedule2_duration)
        return overlap_duration / min_duration if min_duration > 0 else 0.0
    
    def _calculate_engagement_bonus(self, player1: Player, player2: Player) -> float:
        """Calculate engagement bonus based on player activity."""
        engagement1 = float(player1.engagement_score or 0)
        engagement2 = float(player2.engagement_score or 0)
        
        # Normalize engagement scores (assuming max is around 100)
        normalized1 = min(engagement1 / 100.0, 1.0)
        normalized2 = min(engagement2 / 100.0, 1.0)
        
        return (normalized1 + normalized2) / 2.0
    
    def _calculate_match_history_factor(self, player1: Player, player2: Player) -> float:
        """Calculate match history factor."""
        # Get recent matches for both players
        recent_matches1 = self.match_dao.get_player_matches(
            player1.guild_id, player1.user_id, status="completed"
        )
        recent_matches2 = self.match_dao.get_player_matches(
            player2.guild_id, player2.user_id, status="completed"
        )
        
        # Check if they've played together recently
        for match in recent_matches1:
            if player2.user_id in match.players:
                # If they've played together and rated the match highly
                if match.match_quality_score and float(match.match_quality_score) > 7:
                    return 1.0
                elif match.match_quality_score and float(match.match_quality_score) > 5:
                    return 0.5
        
        return 0.0
    
    def _calculate_group_compatibility(self, players: List[Player], 
                                     schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate compatibility for a group of players (doubles)."""
        if len(players) != 4 or len(schedules) != 4:
            return {'overall_score': 0.0, 'reasons': ['Invalid group size']}
        
        # Calculate pairwise compatibilities
        compatibilities = []
        for i in range(len(players)):
            for j in range(i + 1, len(players)):
                compat = self._calculate_compatibility(
                    players[i], players[j], schedules[i], schedules[j]
                )
                compatibilities.append(compat)
        
        # Average the compatibility scores
        avg_score = sum(c['overall_score'] for c in compatibilities) / len(compatibilities)
        
        # Collect reasons
        reasons = []
        if avg_score > 0.6:
            reasons.append("Good overall group compatibility")
        if any(c['ntrp_compatibility'] > 0.8 for c in compatibilities):
            reasons.append("Balanced skill levels")
        
        return {
            'overall_score': avg_score,
            'reasons': reasons
        }
    
    def _find_best_court(self, player1: Player, player2: Player,
                        schedule1: Schedule, schedule2: Schedule) -> Optional[Court]:
        """Find the best court for a match."""
        # Get preferred locations
        player1_locations = player1.preferences.get('locations', [])
        player2_locations = player2.preferences.get('locations', [])
        
        # Find common locations
        common_locations = set(player1_locations) & set(player2_locations)
        
        if common_locations:
            # Get the first common location
            court_id = list(common_locations)[0]
            return self.court_dao.get_court(court_id)
        
        # If no common locations, get any available court
        courts = self.court_dao.list_courts()
        if courts:
            return courts[0]
        
        return None
    
    def _find_best_court_for_group(self, players: List[Player], 
                                  schedules: List[Schedule]) -> Optional[Court]:
        """Find the best court for a group match."""
        # Get all preferred locations
        all_locations = set()
        for player in players:
            all_locations.update(player.preferences.get('locations', []))
        
        if all_locations:
            # Get the first available location
            court_id = list(all_locations)[0]
            return self.court_dao.get_court(court_id)
        
        # Fallback to any available court
        courts = self.court_dao.list_courts()
        if courts:
            return courts[0]
        
        return None
    
    def _find_optimal_match_time(self, schedule1: Schedule, schedule2: Schedule) -> Tuple[int, int]:
        """Find the optimal match time within the overlapping schedules."""
        overlap_start = max(schedule1.start_time, schedule2.start_time)
        overlap_end = min(schedule1.end_time, schedule2.end_time)
        
        # Default to 90 minutes for a match
        match_duration = 90 * 60  # 90 minutes in seconds
        
        # Ensure we don't exceed the overlap
        if overlap_end - overlap_start < match_duration:
            match_duration = overlap_end - overlap_start
        
        # Start the match 15 minutes after the overlap starts to allow for warm-up
        match_start = overlap_start + (15 * 60)
        match_end = match_start + match_duration
        
        return match_start, match_end
    
    def _find_optimal_group_match_time(self, schedules: List[Schedule]) -> Tuple[int, int]:
        """Find the optimal match time for a group."""
        if not schedules:
            return 0, 0
        
        # Find the common overlap
        overlap_start = max(s.start_time for s in schedules)
        overlap_end = min(s.end_time for s in schedules)
        
        # Default to 90 minutes for doubles
        match_duration = 90 * 60
        
        if overlap_end - overlap_start < match_duration:
            match_duration = overlap_end - overlap_start
        
        match_start = overlap_start + (15 * 60)
        match_end = match_start + match_duration
        
        return match_start, match_end
    
    def _group_schedules_by_overlap(self, player_schedule: Schedule, 
                                   available_schedules: List[Schedule]) -> List[List[Schedule]]:
        """Group schedules by time overlap."""
        groups = []
        
        for schedule in available_schedules:
            if schedule.overlaps_with(player_schedule):
                # Check if this schedule fits in any existing group
                added_to_group = False
                for group in groups:
                    # Check if this schedule overlaps with all schedules in the group
                    if all(schedule.overlaps_with(s) for s in group):
                        group.append(schedule)
                        added_to_group = True
                        break
                
                if not added_to_group:
                    groups.append([schedule])
        
        return groups
    
    def _get_players_for_schedules(self, guild_id: str, schedules: List[Schedule]) -> Dict[str, Player]:
        """Get all players for a list of schedules."""
        players = {}
        user_ids = list(set(s.user_id for s in schedules))
        
        for user_id in user_ids:
            player = self.player_dao.get_player(guild_id, user_id)
            if player:
                players[user_id] = player
        
        return players 