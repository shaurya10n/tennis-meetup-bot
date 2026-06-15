"""Unit tests for standardized Discord responses."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.utils.responses import ResponseType, Responses


class TestResponses:
    def test_create_embed_all_types(self):
        for response_type in [
            ResponseType.SUCCESS,
            ResponseType.ERROR,
            ResponseType.WARNING,
            ResponseType.INFO,
            "unknown",
        ]:
            embed = Responses.create_embed(
                "Title",
                "Description",
                response_type,
                fields=[("Field", "Value", True)],
            )
            assert embed.title.endswith("Title")
            assert embed.description == "Description"

    def test_send_methods_use_response_or_followup(self):
        for method_name, is_done in [
            ("send_error", False),
            ("send_success", False),
            ("send_info", False),
            ("send_warning", False),
            ("send_error", True),
            ("send_success", True),
            ("send_info", True),
            ("send_warning", True),
        ]:
            interaction = MagicMock()
            interaction.response.is_done.return_value = is_done
            interaction.response.send_message = AsyncMock()
            interaction.followup.send = AsyncMock()

            method = getattr(Responses, method_name)
            asyncio.run(method(interaction, title="T", description="D"))

            if is_done:
                interaction.followup.send.assert_awaited_once()
            else:
                interaction.response.send_message.assert_awaited_once()
