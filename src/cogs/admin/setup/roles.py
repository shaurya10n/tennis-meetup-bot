# src/cogs/admin/setup/roles.py
"""
Role setup module for server configuration.

This module handles the creation and management of server roles,
including permissions, colors, and position hierarchy.
"""

import logging
from typing import Dict, List, Tuple, Optional

import nextcord
from nextcord import Interaction, Permissions, Colour, Role, Guild

from src.config.permissions import RolePermissions
from src.utils.config_loader import ConfigLoader
from src.utils.responses import Responses, ResponseType

logger = logging.getLogger(__name__)


class RoleSetup:
    """
    Handles server role setup and management.

    This class manages the creation and updating of server roles based on
    configuration, including:
    - Role creation with specified permissions
    - Role hierarchy management
    - Color and permission updates
    - Error handling and reporting

    Attributes:
        bot (nextcord.Client): The Discord bot instance
        config_loader (ConfigLoader): Configuration loader instance
    """

    def __init__(self, bot):
        """
        Initialize RoleSetup.

        Args:
            bot (nextcord.Client): The Discord bot instance
        """
        self.bot = bot
        self.config_loader = ConfigLoader()

    async def _get_bot_role(self, guild: Guild) -> Optional[Role]:
        """
        Get bot's role without trying to reposition it.

        Args:
            guild (Guild): The Discord guild

        Returns:
            Optional[Role]: The bot's role
        """
        try:
            bot_member = guild.me
            bot_role = bot_member.top_role

            # Log current hierarchy for debugging
            logger.info(f"Bot role '{bot_role.name}' is at position {bot_role.position}")
            logger.info(f"All roles (highest to lowest):")
            for role in reversed(guild.roles):
                logger.info(f"- {role.name} (position: {role.position})")

            return bot_role

        except Exception as e:
            logger.error(f"Error checking bot role: {e}", exc_info=True)
            return None

    async def _process_role(
            self,
            guild: Guild,
            role_id: str,
            role_config: Dict,
            bot_role: Role
    ) -> Tuple[bool, str]:
        """
        Process a single role configuration.

        Args:
            guild (Guild): The Discord guild
            role_id (str): The role identifier from configuration
            role_config (Dict): The role configuration dictionary
            bot_role (Role): The bot's role for hierarchy management

        Returns:
            Tuple[bool, str]: Success status and error message if any
        """
        try:
            # Skip if this is the bot's own role
            if role_id == 'bot' and any(r.name == role_config['name'] for r in guild.me.roles):
                return True, f"Skipped bot role {role_config['name']} as it already exists"

            # Get permission overwrite based on role dynamically
            permission_method = getattr(RolePermissions, f"get_{role_id}_permissions")
            permissions = permission_method()
            logger.info(f"Found permissions for role: {role_id}")

            # Convert PermissionOverwrite to Permissions
            role_permissions = Permissions()
            for perm, value in permissions._values.items():
                if value and hasattr(role_permissions, perm):
                    setattr(role_permissions, perm, True)

            # Check if role exists
            existing_role = nextcord.utils.get(
                guild.roles,
                name=role_config['name']
            )

            return await self._update_or_create_role(
                guild,
                existing_role,
                role_config,
                role_permissions,
                bot_role
            )

        except AttributeError:
            error_msg = f"No permissions defined for role: {role_config['name']}"
            logger.warning(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error processing role {role_config['name']}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    async def _update_or_create_role(
            self,
            guild: Guild,
            existing_role: Optional[Role],
            role_config: Dict,
            role_permissions: Permissions,
            bot_role: Role
    ) -> Tuple[bool, str]:
        """
        Update existing role or create new one.

        Args:
            guild (Guild): The Discord guild
            existing_role (Optional[Role]): Existing role if found
            role_config (Dict): Role configuration
            role_permissions (Permissions): Role permissions
            bot_role (Role): The bot's role for hierarchy management

        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            if existing_role:
                # Ensure role is below bot's role
                if existing_role.position >= bot_role.position:
                    await existing_role.edit(
                        position=bot_role.position - 1,
                        reason="Adjusting role hierarchy"
                    )
                    logger.info(f"Adjusted position for role: {existing_role.name}")

                # Update role
                await existing_role.edit(
                    name=role_config['name'],
                    colour=Colour(role_config['color']),
                    permissions=role_permissions,
                    reason="Updating role settings"
                )
                logger.info(f"Updated role: {role_config['name']}")
                return True, f"Updated {role_config['name']} role settings"
            else:
                # Create new role
                new_role = await guild.create_role(
                    name=role_config['name'],
                    colour=Colour(role_config['color']),
                    permissions=role_permissions,
                    reason="Creating new role"
                )

                # Set position (ensure it's below bot's role)
                target_position = min(role_config['position'], bot_role.position - 1)
                await new_role.edit(position=target_position)

                logger.info(f"Created role: {role_config['name']} at position {target_position}")
                return True, f"Created {role_config['name']} role"

        except Exception as e:
            error_msg = f"Error with role {role_config['name']}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    async def setup_roles(self, interaction: Interaction) -> None:
        """
        Set up server roles based on configuration.

        This method:
        1. Positions bot's role correctly in hierarchy
        2. Loads and validates role configuration
        3. Processes roles in order of position
        4. Creates or updates roles as needed
        5. Reports success or failure

        Args:
            interaction (Interaction): The Discord interaction
        """
        try:
            await interaction.response.defer()
            guild = interaction.guild

            # Position bot's role first
            bot_role = await self._get_bot_role(guild)
            if not bot_role:
                await Responses.send_error(
                    interaction,
                    "Setup Failed",
                    "Could not determine bot's role position"
                )
                return

                # Check if bot role needs to be moved
            if bot_role.position <= 1:
                await interaction.followup.send(
                    embed=Responses.create_embed(
                        "Action Required",
                        "Please follow these steps before continuing:\n\n"
                        "1. Go to Server Settings > Roles\n"
                        "2. Find the 'TennisMeetups' role\n"
                        "3. Drag it near the top of the role list\n"
                        "4. Run this command again\n\n"
                        "This is required for the bot to manage other roles properly.",
                        ResponseType.WARNING
                    )
                )
                return

            # Get role configuration
            roles_config = self.config_loader.config.get('roles', {})
            if not roles_config:
                await Responses.send_error(
                    interaction,
                    "Setup Failed",
                    "No role configuration found"
                )
                return

            setup_errors: List[str] = []

            # Process roles in order
            sorted_roles = sorted(
                roles_config.items(),
                key=lambda x: x[1]['position'],
                reverse=True
            )

            for role_id, role_config in sorted_roles:
                success, message = await self._process_role(
                    guild,
                    role_id,
                    role_config,
                    bot_role
                )
                if success:
                    await interaction.followup.send(
                        embed=Responses.create_embed(
                            "Role Updated" if "Updated" in message else "Role Created",
                            message,
                            ResponseType.SUCCESS
                        )
                    )
                else:
                    setup_errors.append(message)

            # Send final status
            await self._send_final_status(interaction, setup_errors)

        except Exception as e:
            logger.error(f"Error in setup_roles: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Role Setup Failed",
                f"An error occurred during role setup: {str(e)}"
            )

    async def _send_final_status(
            self,
            interaction: Interaction,
            setup_errors: List[str]
    ) -> None:
        """
        Send final status message for role setup.

        Args:
            interaction (Interaction): The Discord interaction
            setup_errors (List[str]): List of errors encountered during setup
        """
        if setup_errors:
            error_list = "\n• ".join(setup_errors)
            await interaction.followup.send(
                embed=Responses.create_embed(
                    "Roles Setup Completed with Errors",
                    f"Setup completed but encountered the following errors:\n• {error_list}",
                    ResponseType.WARNING
                )
            )
            logger.warning("Role setup completed with errors")
        else:
            await interaction.followup.send(
                embed=Responses.create_embed(
                    "Roles Setup Complete",
                    "All roles have been set up successfully!",
                    ResponseType.SUCCESS
                )
            )
            logger.info("Role setup completed successfully")
