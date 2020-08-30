"""The login form."""
from typing import Any

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    Field,
    PasswordField,
    StringField,
    SubmitField,
    ValidationError,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

from ..models import User


class LoginForm(FlaskForm):
    email: Field = StringField(
        "Email", validators=[DataRequired(), Length(1, 64), Email()]
    )
    password: Field = PasswordField("Password", validators=[DataRequired()])
    remember_me: Field = BooleanField("Keep me logged in")
    submit: Field = SubmitField("Log In")


class RegistrationForm(FlaskForm):
    email: Field = StringField(
        "Email", validators=[DataRequired(), Length(1, 64), Email()]
    )
    username: Field = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(1, 64),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Usernames must start with a letter, only have letters, \
numbers, dots, or underscores.",
            ),
        ],
    )
    password: Field = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            EqualTo("password2", message="Passwords must match."),
        ],
    )
    password2: Field = PasswordField("Confirm Password", validators=[DataRequired()])
    submit: Field = SubmitField("Register")

    def validate_email(self, field: Field) -> Any:
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("That email address is already registered.")

    def validate_username(self, field: Field) -> Any:
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("That username is already in use.")


class ChangePasswordForm(FlaskForm):
    old_password: Field = PasswordField("Old password", validators=[DataRequired()])
    password: Field = PasswordField(
        "New password",
        validators=[
            DataRequired(),
            EqualTo("password2", message="The passwords must match."),
        ],
    )
    password2: Field = PasswordField(
        "Confirm new password", validators=[DataRequired()]
    )
    submit: Field = SubmitField("Update password")


class PasswordResetRequestForm(FlaskForm):
    email: Field = StringField(
        "Email", validators=[DataRequired(), Length(1, 64), Email()]
    )
    submit: Field = SubmitField("Reset Password")


class PasswordResetForm(FlaskForm):
    password: Field = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            EqualTo("password2", message="The passwords must match."),
        ],
    )
    password2: Field = PasswordField(
        "Confirm New Password", validators=[DataRequired()]
    )
    submit: Field = SubmitField("Reset Password")


class ChangeEmailForm(FlaskForm):
    email: Field = StringField(
        "New Email", validators=[DataRequired(), Length(1, 64), Email()]
    )
    password: Field = PasswordField("Password", validators=[DataRequired()])
    submit: Field = SubmitField("Update Email Address")

    def validate_email(self, field: Field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("This email address is already registered.")
