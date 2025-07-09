from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from decimal import Decimal

from src.database.models.dynamodb.match import Match


class MatchDAO:
    """Data Access Object for Match model in DynamoDB."""
    
    def __init__(self, dynamodb):
        """Initialize MatchDAO with DynamoDB resource."""
        self.table = dynamodb.Table(Match.TABLE_NAME)
    
    def create_match(self, guild_id: str, **kwargs) -> Match:
        """Create a new match in the database.
        
        Args:
            guild_id: Discord server ID
            **kwargs: Additional match attributes
            
        Returns:
            Match: The created match object
        """
        match = Match(guild_id=guild_id, **kwargs)
        
        # Validate match before saving
        is_valid, error_msg = match.is_valid()
        if not is_valid:
            raise ValueError(f"Invalid match: {error_msg}")
        
        self.table.put_item(Item=match.to_dict())
        return match
    
    def get_match(self, guild_id: str, match_id: str) -> Optional[Match]:
        """Get a match by ID.
        
        Args:
            guild_id: Discord server ID
            match_id: Match ID
            
        Returns:
            Match: The match object or None if not found
        """
        try:
            response = self.table.get_item(
                Key={
                    'guild_id': guild_id,
                    'match_id': match_id
                }
            )
            
            if 'Item' in response:
                return Match.from_dict(response['Item'])
            return None
        except Exception as e:
            print(f"Error getting match: {e}")
            return None
    
    def get_match_by_id(self, match_id: str) -> Optional[Match]:
        """Get a match by match ID only (for DM contexts).
        
        Args:
            match_id: Match ID
            
        Returns:
            Match: The match object or None if not found
        """
        try:
            # Scan the table to find the match by match_id
            response = self.table.scan(
                FilterExpression='match_id = :match_id',
                ExpressionAttributeValues={
                    ':match_id': match_id
                }
            )
            
            items = response.get('Items', [])
            if items:
                return Match.from_dict(items[0])
            return None
        except Exception as e:
            print(f"Error getting match by ID: {e}")
            return None
    
    def get_matches_by_schedule(self, schedule_id: str) -> List[Match]:
        """Get all matches for a specific schedule.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            List[Match]: List of matches
        """
        try:
            response = self.table.query(
                IndexName='ScheduleIndex',
                KeyConditionExpression='schedule_id = :schedule_id',
                ExpressionAttributeValues={
                    ':schedule_id': schedule_id
                }
            )
            
            matches = []
            for item in response.get('Items', []):
                matches.append(Match.from_dict(item))
            
            return matches
        except Exception as e:
            print(f"Error getting matches by schedule: {e}")
            return []
    
    def get_matches_by_status(self, guild_id: str, status: str, limit: int = 50) -> List[Match]:
        """Get matches by status.
        
        Args:
            guild_id: Discord server ID
            status: Match status (scheduled, in_progress, completed, cancelled)
            limit: Maximum number of matches to return
            
        Returns:
            List[Match]: List of matches
        """
        try:
            response = self.table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': status
                },
                Limit=limit
            )
            
            matches = []
            for item in response.get('Items', []):
                if item.get('guild_id') == guild_id:
                    matches.append(Match.from_dict(item))
            
            return matches
        except Exception as e:
            print(f"Error getting matches by status: {e}")
            return []
    
    def get_matches_by_court(self, court_id: str, start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[Match]:
        """Get matches for a specific court within a time range.
        
        Args:
            court_id: Court ID
            start_time: Start time as Unix timestamp (optional)
            end_time: End time as Unix timestamp (optional)
            
        Returns:
            List[Match]: List of matches
        """
        try:
            if start_time and end_time:
                response = self.table.query(
                    IndexName='CourtIndex',
                    KeyConditionExpression='court_id = :court_id AND #start_time BETWEEN :start_time AND :end_time',
                    ExpressionAttributeNames={
                        '#start_time': 'start_time'
                    },
                    ExpressionAttributeValues={
                        ':court_id': court_id,
                        ':start_time': start_time,
                        ':end_time': end_time
                    }
                )
            else:
                response = self.table.query(
                    IndexName='CourtIndex',
                    KeyConditionExpression='court_id = :court_id',
                    ExpressionAttributeValues={
                        ':court_id': court_id
                    }
                )
            
            matches = []
            for item in response.get('Items', []):
                matches.append(Match.from_dict(item))
            
            return matches
        except Exception as e:
            print(f"Error getting matches by court: {e}")
            return []
    
    def get_player_matches(self, guild_id: str, user_id: str, status: Optional[str] = None) -> List[Match]:
        """Get all matches for a specific player.
        
        Args:
            guild_id: Discord server ID
            user_id: Discord user ID
            status: Optional status filter
            
        Returns:
            List[Match]: List of matches
        """
        try:
            # Get all matches for the guild
            response = self.table.scan(
                FilterExpression='guild_id = :guild_id',
                ExpressionAttributeValues={
                    ':guild_id': guild_id
                }
            )
            
            matches = []
            for item in response.get('Items', []):
                match = Match.from_dict(item)
                if user_id in match.players:
                    if status is None or match.status == status:
                        matches.append(match)
            
            return matches
        except Exception as e:
            print(f"Error getting player matches: {e}")
            return []
    
    def update_match(self, guild_id: str, match_id: str, **kwargs) -> Optional[Match]:
        """Update a match.
        
        Args:
            guild_id: Discord server ID
            match_id: Match ID
            **kwargs: Fields to update
            
        Returns:
            Match: The updated match object or None if not found
        """
        try:
            # Get current match
            match = self.get_match(guild_id, match_id)
            if not match:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(match, key):
                    setattr(match, key, value)
            
            # Update timestamp
            match.updated_at = datetime.now(timezone.utc).isoformat()
            
            # Validate match
            is_valid, error_msg = match.is_valid()
            if not is_valid:
                raise ValueError(f"Invalid match after update: {error_msg}")
            
            # Save to database
            self.table.put_item(Item=match.to_dict())
            return match
        except Exception as e:
            print(f"Error updating match: {e}")
            return None
    
    def delete_match(self, guild_id: str, match_id: str) -> bool:
        """Delete a match.
        
        Args:
            guild_id: Discord server ID
            match_id: Match ID
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            self.table.delete_item(
                Key={
                    'guild_id': guild_id,
                    'match_id': match_id
                }
            )
            return True
        except Exception as e:
            print(f"Error deleting match: {e}")
            return False
    
    def get_upcoming_matches(self, guild_id: str, hours_ahead: int = 24) -> List[Match]:
        """Get upcoming matches within the next N hours.
        
        Args:
            guild_id: Discord server ID
            hours_ahead: Number of hours to look ahead
            
        Returns:
            List[Match]: List of upcoming matches
        """
        try:
            now = int(datetime.now(timezone.utc).timestamp())
            future_time = now + (hours_ahead * 3600)
            
            response = self.table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='#status = :status AND #start_time BETWEEN :now AND :future',
                ExpressionAttributeNames={
                    '#status': 'status',
                    '#start_time': 'start_time'
                },
                ExpressionAttributeValues={
                    ':status': 'scheduled',
                    ':now': now,
                    ':future': future_time
                }
            )
            
            matches = []
            for item in response.get('Items', []):
                if item.get('guild_id') == guild_id:
                    matches.append(Match.from_dict(item))
            
            return matches
        except Exception as e:
            print(f"Error getting upcoming matches: {e}")
            return []
    
    def get_existing_match_status(self, guild_id: str, player_ids: List[str], 
                                 start_time: int, end_time: int) -> Optional[str]:
        """Get the status of an existing match between these players.
        
        Args:
            guild_id: Discord server ID
            player_ids: List of player user IDs
            start_time: Start time as Unix timestamp
            end_time: End time as Unix timestamp
            
        Returns:
            Optional[str]: Match status if found, None otherwise
        """
        try:
            # Get all matches for the guild
            response = self.table.scan(
                FilterExpression='guild_id = :guild_id',
                ExpressionAttributeValues={
                    ':guild_id': guild_id
                }
            )
            
            # Check for existing matches with these players
            for item in response.get('Items', []):
                match = Match.from_dict(item)
                
                # Check if this match involves the same players
                if set(match.players) == set(player_ids):
                    # Check if it's a recent match (within 24 hours) or pending
                    if match.status in ["pending_confirmation", "scheduled"]:
                        return match.status
                    
                    # Check if it's a recent cancelled match (within 24 hours)
                    if match.status == "cancelled":
                        # Parse the updated_at timestamp
                        try:
                            updated_at = datetime.fromisoformat(match.updated_at.replace('Z', '+00:00'))
                            now = datetime.now(timezone.utc)
                            time_diff = now - updated_at
                            
                            # If cancelled within the last 24 hours, consider it recent
                            if time_diff.total_seconds() < 24 * 3600:
                                return "recently_cancelled"
                        except:
                            # If we can't parse the timestamp, assume it's recent
                            return "recently_cancelled"
            
            return None
        except Exception as e:
            print(f"Error checking existing match status: {e}")
            return None
    
    def get_matches_by_players(self, guild_id: str, player_ids: List[str]) -> List[Match]:
        """Get all matches between specific players.
        
        Args:
            guild_id: Discord server ID
            player_ids: List of player user IDs
            
        Returns:
            List[Match]: List of matches between these players
        """
        try:
            # Get all matches for the guild
            response = self.table.scan(
                FilterExpression='guild_id = :guild_id',
                ExpressionAttributeValues={
                    ':guild_id': guild_id
                }
            )
            
            matches = []
            for item in response.get('Items', []):
                match = Match.from_dict(item)
                
                # Check if this match involves the same players
                if set(match.players) == set(player_ids):
                    matches.append(match)
            
            return matches
        except Exception as e:
            print(f"Error getting matches by players: {e}")
            return []
    
    def get_matches_by_players_and_time(self, guild_id: str, player_ids: List[str], 
                                       start_time: int, end_time: int) -> List[Match]:
        """Get matches between specific players at a specific time.
        
        Args:
            guild_id: Discord server ID
            player_ids: List of player user IDs
            start_time: Start time as Unix timestamp
            end_time: End time as Unix timestamp
            
        Returns:
            List[Match]: List of matches between these players at this time
        """
        try:
            # Get all matches for the guild
            response = self.table.scan(
                FilterExpression='guild_id = :guild_id',
                ExpressionAttributeValues={
                    ':guild_id': guild_id
                }
            )
            
            matches = []
            for item in response.get('Items', []):
                match = Match.from_dict(item)
                
                # Check if this match involves the same players and time
                if (set(match.players) == set(player_ids) and 
                    match.start_time == start_time and 
                    match.end_time == end_time):
                    matches.append(match)
            
            # Sort by creation time (most recent first)
            matches.sort(key=lambda m: m.created_at, reverse=True)
            return matches
        except Exception as e:
            print(f"Error getting matches by players and time: {e}")
            return []
    
    def has_existing_match_request(self, guild_id: str, player_ids: List[str], 
                                  start_time: int, end_time: int) -> bool:
        """Check if there's already a pending or scheduled match between these players.
        
        Args:
            guild_id: Discord server ID
            player_ids: List of player user IDs
            start_time: Start time as Unix timestamp
            end_time: End time as Unix timestamp
            
        Returns:
            bool: True if there's an existing pending or scheduled match, False otherwise
        """
        status = self.get_existing_match_status(guild_id, player_ids, start_time, end_time)
        # Only consider pending_confirmation and scheduled as blocking new requests
        # recently_cancelled matches should allow new requests
        return status in ["pending_confirmation", "scheduled"] 