"""Backward-compatible exports for exercise navigation commands."""

from bot.handlers.workout import (
    end_workout_command,
    next_exercise_command,
    previous_exercise_command,
)

__all__ = [
    "next_exercise_command",
    "previous_exercise_command",
    "end_workout_command",
]
