# src/utils/responses.py
import nextcord
from typing import Optional

class ResponseType:
    """Constants for different types of response messages.

        Attributes:
            SUCCESS (str): Success message type
            ERROR (str): Error message type
            WARNING (str): Warning message type
            INFO (str): Information message type
        """
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class Responses:
    """Utility class for standardized Discord message responses.

    This class provides static methods for creating and sending
    consistently formatted embed messages for different response types.
    """
    @staticmethod
    def create_embed(
        title: str,
        description: str,
        response_type: str,
        fields: Optional[list] = None
    ) -> nextcord.Embed:
        """Create a standardized embed response.

                Args:
                    title (str): The embed title
                    description (str): The embed description
                    response_type (str): Type of response (success/error/warning/info)
                    fields (Optional[list]): List of fields to add to embed, each field
                                           should be (name, value, inline)

                Returns:
                    nextcord.Embed: The formatted embed object

                Example:
                    >>> embed = Responses.create_embed(
                    ...     "Success",
                    ...     "Operation completed",
                    ...     ResponseType.SUCCESS,
                    ...     [("Field", "Value", True)]
                    ... )
                """
        colors = {
            ResponseType.SUCCESS: nextcord.Color.green(),
            ResponseType.ERROR: nextcord.Color.red(),
            ResponseType.WARNING: nextcord.Color.yellow(),
            ResponseType.INFO: nextcord.Color.blue()
        }

        emojis = {
            ResponseType.SUCCESS: "✅",
            ResponseType.ERROR: "❌",
            ResponseType.WARNING: "⚠️",
            ResponseType.INFO: "ℹ️"
        }

        embed = nextcord.Embed(
            title=f"{emojis.get(response_type, '')} {title}",
            description=description,
            color=colors.get(response_type, nextcord.Color.default())
        )

        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

        return embed

    @staticmethod
    async def send_error(
        interaction: nextcord.Interaction,
        title: str = "Error",
        description: str = "An error occurred",
        ephemeral: bool = True
    ):
        """Send an error response"""
        embed = Responses.create_embed(title, description, ResponseType.ERROR)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @staticmethod
    async def send_success(
        interaction: nextcord.Interaction,
        title: str = "Success",
        description: str = "Operation completed successfully",
        ephemeral: bool = True
    ):
        """Send a success response.

                Args:
                    interaction (nextcord.Interaction): The interaction to respond to
                    title (str, optional): The message title. Defaults to "Success"
                    description (str, optional): The message content
                    ephemeral (bool, optional): Whether message should be ephemeral.
                                              Defaults to True

                Example:
                    >>> await Responses.send_success(
                    ...     interaction,
                    ...     "Rating Set",
                    ...     "You've set your rating to 4"
                    ... )
                """
        embed = Responses.create_embed(title, description, ResponseType.SUCCESS)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @staticmethod
    async def send_info(
        interaction: nextcord.Interaction,
        title: str = "Information",
        description: str = "Here's some information",
        ephemeral: bool = True
    ):
        """Send an info response"""
        embed = Responses.create_embed(title, description, ResponseType.INFO)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @staticmethod
    async def send_warning(
        interaction: nextcord.Interaction,
        title: str = "Warning",
        description: str = "Please note this warning",
        ephemeral: bool = True
    ):
        """Send a warning response"""
        embed = Responses.create_embed(title, description, ResponseType.WARNING)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
