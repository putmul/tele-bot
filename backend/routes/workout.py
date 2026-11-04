"""Workout API routes."""

from flask import Blueprint, jsonify

workout_bp = Blueprint("workout", __name__)


@workout_bp.get("/")
def workout_history():
    return jsonify({"data": [], "message": "Workout history endpoint is ready."})
