# src/utils/role_manager.py
"""
Role management utility module.

This module provides utilities for managing Discord roles, including:
- Role assignment and removal
- Role updates and transitions
- Role verification
"""

import nextcord
from nextcord import Member, Role
import logging
from typing import Optional, Tuple
from .config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class RoleManager:
    """
    Utility class for managing Discord roles.

    This class provides methods for handling all role-related operations,
    including adding, removing, updating, and checking roles for members.

    Attributes:
        config_loader (ConfigLoader): Instance of configuration loader

    Example:
        ```python
        role_manager = RoleManager()
        await role_manager.add_role(member, 'visitor')
        ```
    """

    def __init__(self):
        """Initialize RoleManager with configuration."""
        self.config_loader = ConfigLoader()

    def _get_role(self, guild: nextcord.Guild, role_key: str) -> Tuple[Optional[Role], Optional[str]]:
        """
        Get a role object and its name from configuration.

        Args:
            guild (nextcord.Guild): The Discord guild
            role_key (str): Configuration key for the role

        Returns:
            Tuple[Optional[Role], Optional[str]]: Tuple of (role object, role name)
        """
        try:
            role_name = self.config_loader.config['roles'][role_key]['name']
            role = nextcord.utils.get(guild.roles, name=role_name)
            return role, role_name
        except KeyError:
            logger.error(f"Role key '{role_key}' not found in configuration")
            return None, None
        except Exception as e:
            logger.error(f"Error getting role: {e}", exc_info=True)
            return None, None

    async def update_member_role(
            self,
            member: Member,
            from_role: str,
            to_role: str
    ) -> bool:
        """
        Update member's role from one role to another.

        Args:
            member (Member): The member whose roles should be updated
            from_role (str): Role key to remove (e.g., 'visitor')
            to_role (str): Role key to add (e.g., 'member')

        Returns:
            bool: True if successful, False otherwise

        Example:
            ```python
            success = await role_manager.update_member_role(
                member,
                'visitor',
                'member'
            )
            ```
        """
        try:
            # Get role objects and names
            remove_role, from_role_name = self._get_role(member.guild, from_role)
            add_role, to_role_name = self._get_role(member.guild, to_role)

            if not all([remove_role, add_role, from_role_name, to_role_name]):
                logger.error(
                    f"Could not find roles. From role: {from_role_name}, "
                    f"To role: {to_role_name}"
                )
                return False

            # Update roles
            await member.remove_roles(remove_role)
            await member.add_roles(add_role)

            logger.info(
                f"Updated roles for {member.name}: "
                f"Removed {from_role_name}, Added {to_role_name}"
            )
            return True

        except nextcord.Forbidden as e:
            logger.error(f"Permission denied updating roles for {member.name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating member roles: {e}", exc_info=True)
            return False

    async def add_role(self, member: Member, role_key: str) -> bool:
        """
        Add a role to a member.

        Args:
            member (Member): The member to update
            role_key (str): Role key from config (e.g., 'member')

        Returns:
            bool: True if successful, False otherwise

        Example:
            ```python
            success = await role_manager.add_role(member, 'member')
            ```
        """
        try:
            role, role_name = self._get_role(member.guild, role_key)
            if not role:
                logger.error(f"Could not find role: {role_name}")
                return False

            await member.add_roles(role)
            logger.info(f"Added role {role_name} to {member.name}")
            return True

        except nextcord.Forbidden as e:
            logger.error(f"Permission denied adding role to {member.name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error adding role: {e}", exc_info=True)
            return False

    async def remove_role(self, member: Member, role_key: str) -> bool:
        """
        Remove a role from a member.

        Args:
            member (Member): The member to update
            role_key (str): Role key from config (e.g., 'visitor')

        Returns:
            bool: True if successful, False otherwise

        Example:
            ```python
            success = await role_manager.remove_role(member, 'visitor')
            ```
        """
        try:
            role, role_name = self._get_role(member.guild, role_key)
            if not role:
                logger.error(f"Could not find role: {role_name}")
                return False

            await member.remove_roles(role)
            logger.info(f"Removed role {role_name} from {member.name}")
            return True

        except nextcord.Forbidden as e:
            logger.error(f"Permission denied removing role from {member.name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error removing role: {e}", exc_info=True)
            return False

    async def has_role(self, member: Member, role_key: str) -> bool:
        """
        Check if a member has a specific role.

        Args:
            member (Member): The member to check
            role_key (str): Role key from config (e.g., 'member')

        Returns:
            bool: True if member has the role, False otherwise

        Example:
            ```python
            is_member = await role_manager.has_role(member, 'member')
            ```
        """
        try:
            role, role_name = self._get_role(member.guild, role_key)
            if not role_name:
                return False
            return any(role.name == role_name for role in member.roles)

        except Exception as e:
            logger.error(f"Error checking role: {e}", exc_info=True)
            return False
            
    async def assign_skill_role(self, member: Member, ntrp_rating: float) -> bool:
        """
        Assign appropriate skill level role based on NTRP rating.
        
        Args:
            member (Member): The Discord member
            ntrp_rating (float): The player's NTRP rating
            
        Returns:
            bool: True if assignment was successful, False otherwise
            
        Example:
            ```python
            success = await role_manager.assign_skill_role(member, 3.5)
            ```
        """
        try:
            # Remove any existing skill roles
            for role_key in ['beginner', 'adv_beginner', 'intermediate', 'adv_intermediate', 'advanced']:
                await self.remove_role(member, role_key)
            
            # Assign new role based on NTRP rating ranges from constants.py
            if ntrp_rating <= 2.0:  # Beginner (1.0-2.0)
                await self.add_role(member, 'beginner')
                logger.info(f"Assigned Beginner role to {member.name} (NTRP: {ntrp_rating})")
            elif ntrp_rating <= 3.0:  # Advanced Beginner (2.0-3.0)
                await self.add_role(member, 'adv_beginner')
                logger.info(f"Assigned Advanced Beginner role to {member.name} (NTRP: {ntrp_rating})")
            elif ntrp_rating <= 4.0:  # Intermediate (3.0-4.0)
                await self.add_role(member, 'intermediate')
                logger.info(f"Assigned Intermediate role to {member.name} (NTRP: {ntrp_rating})")
            elif ntrp_rating <= 5.0:  # Advanced Intermediate (4.0-5.0)
                await self.add_role(member, 'adv_intermediate')
                logger.info(f"Assigned Advanced Intermediate role to {member.name} (NTRP: {ntrp_rating})")
            else:  # Advanced (5.0+)
                await self.add_role(member, 'advanced')
                logger.info(f"Assigned Advanced role to {member.name} (NTRP: {ntrp_rating})")
                
            return True
        except Exception as e:
            logger.error(f"Error assigning skill role: {e}", exc_info=True)
            return False
