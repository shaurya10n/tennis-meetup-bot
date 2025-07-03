# src/cogs/user/commands/update_profile/views.py
"""Views for the update-profile command."""

import nextcord
from nextcord import Interaction
from typing import Callable
from .constants import UPDATE_OPTIONS, BUTTON_STYLES


class UpdateOptionsView(nextcord.ui.View):
    """View for selecting which profile aspect to update."""

    def __init__(self, callback: Callable[[Interaction, str], None]):
        super().__init__()
        self.callback = callback

        # Add buttons for each update option
        for key, option in UPDATE_OPTIONS.items():
            button = nextcord.ui.Button(
                style=BUTTON_STYLES["unselected"],
                label=option["label"],
                emoji=option["emoji"],
                custom_id=f"update_{key}"
            )
            button.callback = lambda i, k=key: self.callback(i, k)
            self.add_item(button)
