import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from postgrest.exceptions import APIError

from routes.company_routes import company_bp
from routes.job_routes import job_bp
from routes.student_routes import student_bp
from routes.tracker_routes import tracker_bp
from supabase_client import create_authenticated_client

BACKEND_DIR = Path(__file__).resolve().parent


def create_app(test_config=None):
    load_dotenv(BACKEND_DIR / ".env")

    app = Flask(__name__)
    app.config.from_mapping(
        SUPABASE_URL=os.environ.get("SUPABASE_URL", "").strip(),
        SUPABASE_KEY=os.environ.get("SUPABASE_KEY", "").strip(),
        SUPABASE_CLIENT_FACTORY=create_authenticated_client,
    )
    if test_config:
        app.config.update(test_config)

    missing = [
        key
        for key in ("SUPABASE_URL", "SUPABASE_KEY")
        if not app.config.get(key)
    ]
    if missing:
        raise RuntimeError(
            "Missing required Supabase environment variable(s): "
            f"{', '.join(missing)}. Add them to "
            f"{BACKEND_DIR / '.env'} before starting the Flask backend."
        )

    CORS(app)

    app.register_blueprint(student_bp, url_prefix="/students")
    app.register_blueprint(job_bp, url_prefix="/jobs")
    app.register_blueprint(tracker_bp, url_prefix="/tracker")
    app.register_blueprint(company_bp, url_prefix="/company")

    @app.route("/", methods=["GET"])
    def home():
        return jsonify({
            "message": "Job Matching Platform Backend is Running!",
            "status": "success",
        })

    @app.route("/hello", methods=["GET"])
    def hello():
        return jsonify({"message": "Hello from Flask!"})

    @app.errorhandler(APIError)
    def handle_database_error(error):
        error_code = getattr(error, "code", None)
        status_by_code = {
            "23505": 409,
            "23503": 409,
            "23502": 400,
            "23514": 400,
            "22P02": 400,
            "22007": 400,
            "42501": 403,
            "PGRST116": 404,
        }
        status = status_by_code.get(error_code, 503)
        messages = {
            400: "The submitted data is invalid.",
            403: "You are not allowed to perform this operation.",
            404: "The requested record was not found.",
            409: "The operation conflicts with existing related data.",
            503: "The database request could not be completed.",
        }
        app.logger.warning(
            "Supabase request failed (code=%s).", error_code or "unknown"
        )
        return jsonify({"error": messages[status]}), status

    @app.errorhandler(httpx.HTTPError)
    def handle_database_connection_error(error):
        app.logger.error(
            "Supabase connection failed (%s).", type(error).__name__
        )
        return jsonify({"error": "The database service is unavailable."}), 503

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "").lower() == "true", port=5000)
