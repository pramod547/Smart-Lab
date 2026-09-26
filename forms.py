"""
WTForms definitions for authentication and note uploads with CSRF protection.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from models import User, db


class RegistrationForm(FlaskForm):
    """User registration form with uniqueness checks."""
    
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username is required."),
            Length(min=3, max=80, message="Username must be between 3 and 80 characters.")
        ]
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email address is required."),
            Email(message="Please provide a valid email address."),
            Length(max=120)
        ]
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=6, max=128, message="Password must be at least 6 characters.")
        ]
    )
    password2 = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match.")
        ]
    )
    submit = SubmitField("Create account")

    def validate_username(self, field):
        cleaned_username = (field.data or "").strip()
        user = db.session.execute(
            db.select(User).filter_by(username=cleaned_username)
        ).scalar_one_or_none()
        if user:
            raise ValidationError("That username is already taken.")

    def validate_email(self, field):
        cleaned_email = (field.data or "").strip().lower()
        user = db.session.execute(
            db.select(User).filter_by(email=cleaned_email)
        ).scalar_one_or_none()
        if user:
            raise ValidationError("That email is already registered.")


class LoginForm(FlaskForm):
    """User login form."""
    
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username is required."),
            Length(max=80)
        ]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required.")]
    )
    submit = SubmitField("Log in")


class NoteUploadForm(FlaskForm):
    """Study note upload form accepting PDF files only."""
    
    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(min=2, max=200, message="Title must be between 2 and 200 characters.")
        ]
    )
    subject = StringField(
        "Subject",
        validators=[
            DataRequired(message="Subject is required."),
            Length(min=2, max=120, message="Subject must be between 2 and 120 characters.")
        ]
    )
    pdf = FileField(
        "PDF file",
        validators=[
            FileRequired(message="Please select a PDF file to upload."),
            FileAllowed(["pdf"], "Only PDF files (.pdf) are allowed.")
        ]
    )
    submit = SubmitField("Upload note")
