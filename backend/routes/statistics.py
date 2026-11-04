"""Statistics API routes."""

from flask import Blueprint, jsonify

statistics_bp = Blueprint("statistics", __name__)


@statistics_bp.get("/")
def workout_statistics():
    return jsonify({"data": {}, "message": "Statistics endpoint is ready."})
