"""
Database models for Smart Lab.

We use three related tables:
- User: accounts and authentication.
- UploadedFile: each file saved under static/uploads/ (secure name + original name).
- Note: study note metadata (title, subject) linked to one uploaded file and one uploader.
"""

from datetime import datetime, timezone

from flask_login import UserMixin

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    """Timezone-aware 'now' for consistent timestamps in SQLite."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """A registered user who can log in, upload notes, and browse the library."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # One user can upload many notes/files
    notes = db.relationship("Note", backref="author", lazy="dynamic", foreign_keys="Note.uploaded_by_id")
    files = db.relationship("UploadedFile", backref="uploader", lazy="dynamic", foreign_keys="UploadedFile.user_id")

    def set_password(self, password: str) -> None:
        """Hash and store the password (never store plain text)."""
        from werkzeug.security import generate_password_hash

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check a login password against the stored hash."""
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password_hash, password)


class UploadedFile(db.Model):
    """Metadata for a file stored on disk (typically a PDF under static/uploads/)."""

    __tablename__ = "uploaded_files"

    id = db.Column(db.Integer, primary_key=True)
    # Name on disk (unique, safe for filesystem)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    # Original upload name (shown to users)
    original_filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=utcnow, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # One uploaded file is attached to at most one note (PDF study material).
    note = db.relationship("Note", back_populates="uploaded_file", uselist=False)


class Note(db.Model):
    """A study note entry: title, subject, and link to the uploaded PDF file."""

    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    upload_date = db.Column(db.DateTime, default=utcnow, nullable=False)

    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey("uploaded_files.id"), nullable=False, unique=True)

    uploaded_file = db.relationship("UploadedFile", back_populates="note")

    @property
    def filename(self) -> str:
        """Compatibility with the spec: expose the stored file name for templates/routes."""
        f = self.uploaded_file
        return f.stored_filename if f else ""
