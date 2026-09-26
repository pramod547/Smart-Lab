"""
Smart Lab — Application Factory & Server Entry Point.

This module initializes:
- Configuration via config.py
- Database (SQLAlchemy) & authentication (Flask-Login)
- Blueprints and application routes
- Security headers (clickjacking protection, MIME sniffing protection)
- Custom error handlers (404, 413, 500)
"""

import os
from flask import Flask, render_template
from flask_login import LoginManager

from config import config_by_name
from models import User, db
from routes import (
    download_note,
    index,
    login,
    logout,
    notes,
    register,
    serve_pdf,
    upload_note,
    view_note,
)


def create_app(config_name: str | None = None) -> Flask:
    """Application factory for Smart Lab."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "danger"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # --- Route Registrations (compatible with url_for('name') and url_for('main.name')) ---
    app.add_url_rule("/", "index", index)
    app.add_url_rule("/register", "register", register, methods=["GET", "POST"])
    app.add_url_rule("/login", "login", login, methods=["GET", "POST"])
    app.add_url_rule("/logout", "logout", logout)
    app.add_url_rule("/upload", "upload_note", upload_note, methods=["GET", "POST"])
    app.add_url_rule("/notes", "notes", notes)
    app.add_url_rule("/notes/<int:note_id>", "view_note", view_note)
    app.add_url_rule("/notes/<int:note_id>/pdf", "serve_pdf", serve_pdf)
    app.add_url_rule("/notes/<int:note_id>/download", "download_note", download_note)

    # Also register routes under 'main.' endpoint for blueprint compatibility
    app.add_url_rule("/", "main.index", index)
    app.add_url_rule("/register", "main.register", register, methods=["GET", "POST"])
    app.add_url_rule("/login", "main.login", login, methods=["GET", "POST"])
    app.add_url_rule("/logout", "main.logout", logout)
    app.add_url_rule("/upload", "main.upload_note", upload_note, methods=["GET", "POST"])
    app.add_url_rule("/notes", "main.notes", notes)
    app.add_url_rule("/notes/<int:note_id>", "main.view_note", view_note)
    app.add_url_rule("/notes/<int:note_id>/pdf", "main.serve_pdf", serve_pdf)
    app.add_url_rule("/notes/<int:note_id>/download", "main.download_note", download_note)

    # --- Security Headers -------------------------------------------------------
    @app.after_request
    def set_security_headers(response):
        # Prevent clickjacking while allowing iframe previews from same origin
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        # Prevent MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # --- Error Handlers ---------------------------------------------------------
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return render_template("413.html"), 413

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    # Auto-create tables in development
    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    # Run the application directly with: python app.py
    app.run(host="127.0.0.1", port=5000, debug=True)
