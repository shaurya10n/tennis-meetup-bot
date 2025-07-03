# src/cogs/admin/setup/channels.py
import nextcord
from nextcord import Interaction
import logging
from src.utils.responses import Responses, ResponseType
from src.utils.config_loader import ConfigLoader
from src.config.permissions import RolePermissions


logger = logging.getLogger(__name__)


class ChannelSetup:
    def __init__(self, bot):
        self.bot = bot
        self.config_loader = ConfigLoader()  # Create instance to use throughout the class

    async def get_or_create_category(self, guild: nextcord.Guild, category_name: str) -> nextcord.CategoryChannel:
        """Get existing category or create new one"""
        category = nextcord.utils.get(guild.categories, name=category_name)
        if not category:
            logger.info(f"Creating category: {category_name}")
            category = await guild.create_category(category_name)

        return category

    async def setup_channel_permissions(
            self,
            channel: nextcord.TextChannel,
            guild: nextcord.Guild,
            access_roles: list
    ) -> None:
        """Set up channel permissions for roles"""
        try:
            # Default permissions (no access)
            overwrites = {
                guild.default_role: nextcord.PermissionOverwrite(
                    read_messages=False,
                    send_messages=False
                )
            }

            # Add permissions for specified roles
            for role_name in access_roles:
                role = nextcord.utils.get(guild.roles, name=role_name)
                if role:
                    role_id = self.config_loader.get_role_id(role_name)
                    permission_method = getattr(RolePermissions, f"get_{role_id}_permissions")
                    overwrites[role] = permission_method()
                else:
                    logger.warning(f"Role not found: {role_name}")

            await channel.edit(overwrites=overwrites)
            logger.info(f"Updated permissions for channel: {channel.name}")

        except Exception as e:
            logger.error(f"Error setting channel permissions: {e}")
            raise

    async def setup_channels(self, interaction: Interaction) -> None:
        """Set up server channels"""
        try:
            await interaction.response.defer()
            guild = interaction.guild

            # Get channels configuration using property
            channels_config = self.config_loader.config.get('channels', {})
            if not channels_config:
                raise ValueError("No channels configuration found")

            for channel_id, channel_config in channels_config.items():
                try:
                    # Log channel configuration for debugging
                    logger.debug(f"Setting up channel: {channel_id}")
                    logger.debug(f"Channel config: {channel_config}")

                    # Get or create category
                    category = await self.get_or_create_category(
                        guild,
                        channel_config.get('category', 'General')
                    )

                    # Check if channel exists
                    channel_name = channel_config.get('name')
                    if not channel_name:
                        raise ValueError(f"No name specified for channel {channel_id}")

                    channel = nextcord.utils.get(
                        category.channels,
                        name=channel_name
                    )

                    if channel:
                        # Update existing channel
                        await channel.edit(
                            name=channel_name,
                            topic=channel_config.get('topic', ''),
                            category=category,
                            reason="Updating channel settings"
                        )
                        await self.setup_channel_permissions(
                            channel,
                            guild,
                            channel_config.get('access_roles', [])
                        )

                        await interaction.followup.send(
                            embed=Responses.create_embed(
                                "Channel Updated",
                                f"Updated {channel_name} channel settings",
                                ResponseType.SUCCESS
                            )
                        )
                        logger.info(f"Updated channel: {channel_name}")

                    else:
                        # Create new channel
                        channel = await category.create_text_channel(
                            name=channel_name,
                            topic=channel_config.get('topic', '')
                        )
                        await self.setup_channel_permissions(
                            channel,
                            guild,
                            channel_config.get('access_roles', [])
                        )

                        await interaction.followup.send(
                            embed=Responses.create_embed(
                                "Channel Created",
                                f"Created {channel_name} channel in {category.name}",
                                ResponseType.SUCCESS
                            )
                        )
                        logger.info(f"Created channel: {channel_name}")

                except nextcord.Forbidden as e:
                    error_msg = f"Bot doesn't have permission to manage channel: {channel_config.get('name', 'unknown')}"
                    logger.error(f"{error_msg}: {str(e)}")
                    await interaction.followup.send(
                        embed=Responses.create_embed(
                            "Permission Error",
                            error_msg,
                            ResponseType.ERROR
                        )
                    )
                except Exception as e:
                    logger.error(f"Error setting up channel {channel_config.get('name', 'unknown')}: {e}",
                                 exc_info=True)
                    await interaction.followup.send(
                        embed=Responses.create_embed(
                            "Channel Setup Error",
                            f"Error setting up {channel_config.get('name', 'unknown')}: {str(e)}",
                            ResponseType.ERROR
                        )
                    )

            await interaction.followup.send(
                embed=Responses.create_embed(
                    "Channels Setup Complete",
                    "All channels have been set up successfully!",
                    ResponseType.SUCCESS
                )
            )
            logger.info("Channel setup completed successfully")

        except Exception as e:
            logger.error(f"Error in setup_channels: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Channel Setup Failed",
                f"An error occurred during channel setup: {str(e)}"
            )
