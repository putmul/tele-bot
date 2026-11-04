"""Flask API entry point."""

from flask import Flask, jsonify

from backend.routes.body import body_bp
from backend.routes.cardio import cardio_bp
from backend.routes.statistics import statistics_bp
from backend.routes.workout import workout_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(workout_bp, url_prefix="/api/workouts")
    app.register_blueprint(statistics_bp, url_prefix="/api/statistics")
    app.register_blueprint(cardio_bp, url_prefix="/api/cardio")
    app.register_blueprint(body_bp, url_prefix="/api/body")

    @app.get("/health")
    def health_check():
        return jsonify({"status": "ok", "service": "GymBuddy_Bot API"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
