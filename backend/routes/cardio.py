"""Cardio API routes."""

from flask import Blueprint, jsonify

cardio_bp = Blueprint("cardio", __name__)


@cardio_bp.get("/")
def cardio_history():
    return jsonify({"data": [], "message": "Cardio endpoint is ready."})
