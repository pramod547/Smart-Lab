"""
Application routes, view controllers, and security helpers.
"""

import os
import uuid
from urllib.parse import urlsplit

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from forms import LoginForm, NoteUploadForm, RegistrationForm
from models import Note, UploadedFile, User, db

main_bp = Blueprint("main", __name__)


# --- Security Helpers -----------------------------------------------------------

def is_safe_redirect_url(target: str | None) -> bool:
    """
    Ensure the redirect target URL is internal and safe to prevent open redirect vulnerabilities.
    """
    if not target:
        return False
    # Target must be relative and have no scheme or netloc
    target_split = urlsplit(target)
    return (
        target_split.scheme == ""
        and target_split.netloc == ""
        and target.startswith("/")
        and not target.startswith("//")
        and "\\" not in target
    )


def validate_and_save_pdf(file_storage) -> tuple[str, str]:
    """
    Validate file extension and PDF magic bytes (%PDF-), then safely persist to disk.
    
    Returns:
        (stored_unique_filename, sanitized_original_filename)
    """
    original_name = secure_filename(file_storage.filename or "document.pdf")
    if not original_name.lower().endswith(".pdf"):
        raise ValueError("Invalid file extension. Only .pdf files are accepted.")

    # Read the first 5 bytes to verify standard PDF header signature
    header = file_storage.read(5)
    file_storage.seek(0)  # Reset stream position

    if header != b"%PDF-":
        raise ValueError("Invalid file content. The uploaded file is not a valid PDF document.")

    # Generate a collision-resistant unique filename
    unique_prefix = uuid.uuid4().hex
    stored_name = f"{unique_prefix}_{original_name}"
    
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    dest_path = os.path.join(upload_dir, stored_name)
    file_storage.save(dest_path)
    return stored_name, original_name


# --- Public & Informational Routes ----------------------------------------------

@main_bp.route("/")
def index():
    """Marketing and landing page."""
    return render_template("index.html")


# --- Authentication Routes ------------------------------------------------------

@main_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            role="user"
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created successfully. You can now log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html", form=form)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    """User authentication."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        username_query = form.username.data.strip()
        user = db.session.execute(
            db.select(User).filter_by(username=username_query)
        ).scalar_one_or_none()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password. Please try again.", "danger")
            return redirect(url_for("main.login"))

        login_user(user, remember=True)
        flash(f"Welcome back, {user.username}!", "success")

        next_page = request.args.get("next")
        if next_page and is_safe_redirect_url(next_page):
            return redirect(next_page)
        return redirect(url_for("main.index"))

    return render_template("login.html", form=form)


@main_bp.route("/logout")
@login_required
def logout():
    """End current user session."""
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("main.index"))


# --- Note Management & Viewing Routes ------------------------------------------

@main_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_note():
    """Upload a new study note (PDF) with metadata."""
    form = NoteUploadForm()
    if form.validate_on_submit():
        try:
            stored_name, orig_name = validate_and_save_pdf(form.pdf.data)
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("upload.html", form=form)

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

        flash("Your note was uploaded successfully!", "success")
        return redirect(url_for("main.notes"))

    return render_template("upload.html", form=form)


@main_bp.route("/notes")
def notes():
    """Browse all available notes with optional search/filter."""
    search_query = request.args.get("q", "").strip()
    
    stmt = db.select(Note).order_by(Note.upload_date.desc())
    if search_query:
        search_pattern = f"%{search_query}%"
        stmt = stmt.filter(
            (Note.title.ilike(search_pattern)) | (Note.subject.ilike(search_pattern))
        )
        
    all_notes = db.session.execute(stmt).scalars().all()
    return render_template("notes.html", notes=all_notes, search_query=search_query)


@main_bp.route("/notes/<int:note_id>")
def view_note(note_id: int):
    """View note details and inline PDF."""
    note = db.session.get(Note, note_id)
    if note is None:
        abort(404)
    return render_template("view.html", note=note)


@main_bp.route("/notes/<int:note_id>/pdf")
def serve_pdf(note_id: int):
    """Directly stream the PDF document with proper headers for inline rendering."""
    note = db.session.get(Note, note_id)
    if note is None or note.uploaded_file is None:
        abort(404)

    uf = note.uploaded_file
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(
        upload_dir,
        uf.stored_filename,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=uf.original_filename,
    )


@main_bp.route("/notes/<int:note_id>/download")
def download_note(note_id: int):
    """Download the PDF file attachment with original filename."""
    note = db.session.get(Note, note_id)
    if note is None or note.uploaded_file is None:
        abort(404)

    uf = note.uploaded_file
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(
        upload_dir,
        uf.stored_filename,
        as_attachment=True,
        download_name=uf.original_filename,
    )
