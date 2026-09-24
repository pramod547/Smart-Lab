"""
Smart Lab — Flask application entry point.

This file wires together:
- configuration (SQLite, uploads, CSRF secret)
- Flask-Login session handling
- WTForms forms with CSRF protection
- routes for the public site, authentication, uploads, and note browsing
"""

import os
import uuid

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from werkzeug.utils import secure_filename
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from models import Note, UploadedFile, User, db

# Only PDFs are accepted for study materials (easy to extend later).
ALLOWED_EXTENSIONS = {"pdf"}
MAX_UPLOAD_MB = 16

# --- Flask app & configuration -------------------------------------------------

app = Flask(__name__)

# IMPORTANT: set a strong random secret in production, e.g. via environment variable.
app.config["SECRET_KEY"] = os.environ.get("SMARTLAB_SECRET_KEY", "dev-change-me-in-production")

_base_dir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(_base_dir, "smartlab.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

db.init_app(app)

# Folder where uploaded PDFs are stored (served as static files for viewing).
UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Flask-Login ----------------------------------------------------------------

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "danger"


@login_manager.user_loader
def load_user(user_id: str):
    """Tell Flask-Login how to fetch a user from the database by id."""
    return User.query.get(int(user_id))


# --- Forms (Flask-WTF provides CSRF tokens via hidden_tag()) --------------------

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    password2 = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError("That username is already taken.")

    def validate_email(self, field):
        email = (field.data or "").strip().lower()
        if User.query.filter_by(email=email).first():
            raise ValidationError("That email is already registered.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class NoteUploadForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=2, max=200)])
    subject = StringField("Subject", validators=[DataRequired(), Length(min=2, max=120)])
    pdf = FileField(
        "PDF file",
        validators=[
            FileRequired(),
            FileAllowed(list(ALLOWED_EXTENSIONS), "PDF files only."),
        ],
    )
    submit = SubmitField("Upload note")


# --- Helpers --------------------------------------------------------------------

def allowed_file(filename: str) -> bool:
    """Return True if the uploaded filename has an allowed extension."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def save_uploaded_pdf(file_storage) -> tuple[str, str]:
    """
    Save an uploaded PDF to disk with a unique secure name.

    Returns (stored_filename_on_disk, original_safe_filename).
    """
    original = secure_filename(file_storage.filename or "document.pdf") or "document.pdf"
    if not allowed_file(original):
        raise ValueError("Only PDF uploads are allowed.")

    ext = original.rsplit(".", 1)[1].lower()
    stored = f"{uuid.uuid4().hex}_{original}"
    if ext != "pdf":
        raise ValueError("Invalid file type.")

    dest_path = os.path.join(UPLOAD_FOLDER, stored)
    file_storage.save(dest_path)
    return stored, original


# --- Routes ---------------------------------------------------------------------

@app.route("/")
def index():
    """Marketing / landing page (same sections as your original static site)."""
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Create a new user account with a hashed password."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data.strip(), email=form.email.data.strip().lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created. You can log in now.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a user and start a session."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password.", "danger")
            return redirect(url_for("login"))

        login_user(user, remember=True)
        next_page = request.args.get("next")
        # Basic open-redirect protection: only allow relative paths on same site.
        if next_page and next_page.startswith("/") and not next_page.startswith("//"):
            return redirect(next_page)
        return redirect(url_for("index"))

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    """End the current user session."""
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload_note():
    """Upload a PDF note and store metadata in SQLite."""
    form = NoteUploadForm()
    if form.validate_on_submit():
        try:
            stored_name, orig_name = save_uploaded_pdf(form.pdf.data)
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("upload_note"))

        uploaded = UploadedFile(
            stored_filename=stored_name,
            original_filename=orig_name,
            user_id=current_user.id,
        )
        db.session.add(uploaded)
        db.session.flush()

        note = Note(
            title=form.title.data.strip(),
            subject=form.subject.data.strip(),
            uploaded_by_id=current_user.id,
            file_id=uploaded.id,
        )
        db.session.add(note)
        db.session.commit()

        flash("Your note was uploaded successfully.", "success")
        return redirect(url_for("notes"))

    return render_template("upload.html", form=form)


@app.route("/notes")
def notes():
    """List all notes from the database (newest first)."""
    all_notes = Note.query.order_by(Note.upload_date.desc()).all()
    return render_template("notes.html", notes=all_notes)


@app.route("/notes/<int:note_id>")
def view_note(note_id: int):
    """Show a single PDF inline in the browser."""
    note = Note.query.get(note_id)
    if note is None:
        abort(404)
    return render_template("view.html", note=note)


@app.route("/notes/<int:note_id>/download")
def download_note(note_id: int):
    """Download the stored PDF using the original filename."""
    note = Note.query.get(note_id)
    if note is None or note.uploaded_file is None:
        abort(404)

    uf = note.uploaded_file
    return send_from_directory(
        UPLOAD_FOLDER,
        uf.stored_filename,
        as_attachment=True,
        download_name=uf.original_filename,
    )


# --- Dev entrypoint -------------------------------------------------------------

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    # Run with: python app.py
    app.run(debug=True)
