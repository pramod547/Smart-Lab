"""
Database models for Smart Lab.

Tables:
- User: Account details, hashed password, and role.
- UploadedFile: Metadata for stored physical files on disk.
- Note: Study note metadata linking an author with an uploaded PDF file.
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def utcnow() -> datetime:
    """Timezone-aware UTC timestamp for database records."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Registered user account."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)

    # Relationships
    notes = db.relationship(
        "Note",
        backref="author",
        lazy="select",
        foreign_keys="Note.uploaded_by_id",
        cascade="all, delete-orphan"
    )
    files = db.relationship(
        "UploadedFile",
        backref="uploader",
        lazy="select",
        foreign_keys="UploadedFile.user_id",
        cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username} (id={self.id})>"


class UploadedFile(db.Model):
    """Metadata for uploaded files stored securely on disk."""

    __tablename__ = "uploaded_files"

    id = db.Column(db.Integer, primary_key=True)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=utcnow, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Link to Note
    note = db.relationship("Note", back_populates="uploaded_file", uselist=False)

    def __repr__(self) -> str:
        return f"<UploadedFile {self.original_filename} (stored={self.stored_filename})>"


class Note(db.Model):
    """Study note entry containing subject metadata and linked PDF."""

    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    upload_date = db.Column(db.DateTime, default=utcnow, nullable=False)

    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False, unique=True)

    uploaded_file = db.relationship("UploadedFile", back_populates="note")

    @property
    def filename(self) -> str:
        """Helper property to access the stored filename."""
        return self.uploaded_file.stored_filename if self.uploaded_file else ""

    def __repr__(self) -> str:
        return f"<Note '{self.title}' (subject={self.subject})>"
