"""Body measurement API routes."""

from flask import Blueprint, jsonify

body_bp = Blueprint("body", __name__)


@body_bp.get("/")
def body_history():
    return jsonify({"data": [], "message": "Body measurement endpoint is ready."})
