# src/cogs/user/commands/get_started/ntrp/questions_step.py
import nextcord
from nextcord import Interaction, Embed, Color
import logging
from src.utils.responses import Responses
from ..constants import NTRP_QUESTIONS, BUTTON_STYLES, NTRP_CONFIG

logger = logging.getLogger(__name__)


class QuestionView(nextcord.ui.View):
    """View for displaying and handling NTRP assessment questions."""

    def __init__(self, question_id: str, question_data: dict, callback, current_num: int, total: int):
        super().__init__()
        self.callback = callback
        self.question_id = question_id

        # Add answer buttons
        for answer in question_data["answers"]:
            button = nextcord.ui.Button(
                label=answer["text"],
                custom_id=f"answer_{self.question_id}_{answer['value']}",
                style=BUTTON_STYLES["unselected"],
                row=len(self.children) // 3
            )
            button.callback = self.answer_callback
            self.add_item(button)

    async def answer_callback(self, interaction: Interaction):
        """Handle answer selection."""
        try:
            custom_id = interaction.data["custom_id"]
            _, question_id, value = custom_id.split("_")
            await self.callback(interaction, question_id, float(value))

        except Exception as e:
            logger.error(f"Error handling answer: {e}", exc_info=True)
            await Responses.send_error(
                interaction,
                "Error",
                "An error occurred. Please try again."
            )


class NTRPQuestionsHandler:
    """Handler for NTRP assessment questions flow."""

    def __init__(self, final_callback):
        self.final_callback = final_callback
        self.questions = list(NTRP_QUESTIONS.items())
        self.current_question = 0
        self.responses = {}

    def calculate_rating(self) -> float:
        """Calculate NTRP rating based on responses."""
        total_weight = sum(q_data["weight"] for _, q_data in self.questions)
        weighted_sum = sum(
            self.responses[q_id] * q_data["weight"]
            for q_id, q_data in self.questions
        )

        # Calculate raw rating
        raw_rating = weighted_sum / total_weight

        # Apply some adjustments based on patterns
        if all(self.responses[q_id] <= 2.5 for q_id, _ in self.questions):
            # If all answers are beginner level, cap at advanced beginner
            raw_rating = min(raw_rating, 2.5)
        elif all(self.responses[q_id] >= 4.5 for q_id, _ in self.questions):
            # If all answers are advanced level, ensure minimum advanced intermediate
            raw_rating = max(raw_rating, 4.5)

        # Round to nearest 0.5
        rounded_rating = round(raw_rating * 2) / 2

        # Clamp to configured range
        return max(
            min(rounded_rating, NTRP_CONFIG["max_rating"]),
            NTRP_CONFIG["min_rating"]
        )

    async def show_question(self, interaction: Interaction):
        """Show the current question."""
        if self.current_question >= len(self.questions):
            # All questions answered, calculate rating
            rating = self.calculate_rating()
            await self.final_callback(interaction, rating, self.responses)
            return

        question_id, question_data = self.questions[self.current_question]
        embed = Embed(
            title=f"Question {self.current_question + 1}/{len(self.questions)}",
            description=question_data["text"],
            color=Color.blue()
        )

        view = QuestionView(
            question_id,
            question_data,
            self.handle_answer,
            self.current_question + 1,
            len(self.questions)
        )

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def handle_answer(self, interaction: Interaction, question_id: str, answer_value: float):
        """Handle answer selection and move to next question."""
        self.responses[question_id] = answer_value
        self.current_question += 1
        await self.show_question(interaction)


async def ntrp_questions_step(interaction: Interaction, callback):
    """Start the NTRP questions flow."""
    try:
        handler = NTRPQuestionsHandler(callback)
        await handler.show_question(interaction)
    except Exception as e:
        logger.error(f"Error in ntrp_questions_step: {e}", exc_info=True)
        await Responses.send_error(
            interaction,
            "Setup Error",
            "An error occurred. Please try again."
        )
