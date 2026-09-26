"""
Configuration settings for Smart Lab application.
Supports Development, Testing, and Production environments.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration with secure defaults."""
    
    # Secret Key for session management and CSRF protection
    SECRET_KEY = os.environ.get("SMARTLAB_SECRET_KEY", "dev-change-me-in-production")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'smartlab.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads settings
    MAX_UPLOAD_MB = 16
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_EXTENSIONS = {"pdf"}

    # Cookie & Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600 * 24 * 14  # 14 days


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
