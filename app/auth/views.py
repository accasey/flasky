"""The auth blueprint's routes."""
from typing import Any

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf.form import FlaskForm
from werkzeug.wrappers import Response

from . import auth
from .forms import (
    ChangeEmailForm,
    ChangePasswordForm,
    LoginForm,
    PasswordResetForm,
    PasswordResetRequestForm,
    RegistrationForm,
)
from .. import db
from ..email import send_email
from ..models import User


@auth.before_app_request
def before_request() -> Response:
    if current_user.is_authenticated:
        current_user.ping()
        if (
            not current_user.confirmed
            and request.endpoint
            and request.blueprint != "auth"
            and request.endpoint != "static"
        ):
            return redirect(url_for("auth.unconfirmed"))


@auth.route("/unconfirmed")
def unconfirmed() -> Any:
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for("main.index"))

    return render_template("auth/unconfirmed.html")


@auth.route("/login", methods=["GET", "POST"])
def login() -> Any:
    form: FlaskForm = LoginForm()
    if form.validate_on_submit():
        user: User = User.query.filter_by(email=form.email.data).first()

        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next: Any = request.args.get("next")
            # e.g. /auth/logout if acessing the logout route

            if next is None or not next.startswith("/"):
                next = url_for("main.index")

            return redirect(next)

        flash("Invalid username or passowrd")

    return render_template("auth/login.html", form=form)


@auth.route("/logout")
@login_required
def logout() -> Response:
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.index"))


@auth.route("/register", methods=["GET", "POST"])
def register() -> Any:
    form: FlaskForm = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            username=form.username.data,
            password=form.password.data,
        )
        db.session.add(user)
        db.session.commit()

        token = user.generate_confirmation_token()
        send_email(
            user.email,
            "Confirm your Account",
            "auth/email/confirm",
            user=user,
            token=token,
        )

        flash("A confirmation email has been sent to you.")

        return redirect(url_for("main.index"))

    return render_template("auth/register.html", form=form)


@auth.route("/confirm/<token>")
@login_required
def confirm(token: str) -> Response:
    if current_user.confirmed:
        return redirect(url_for("main.index"))

    if current_user.confirm(token):
        db.session.commit()
        flash("Thanks, you have confirmed your account.")
    else:
        flash("The confirmation link is invalid or has expired.")

    return redirect(url_for("main.index"))


@auth.route("/confirm")
@login_required
def resend_confirmation() -> Response:
    token = current_user.generate_confirmation_token()
    send_email(
        current_user.email,
        "Confirm your account",
        "auth/email/confirm",
        user=current_user,
        token=token,
    )
    flash("A new confirmation email has been sent to you.")

    return redirect(url_for("main.index"))


@auth.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password() -> Any:
    form: FlaskForm = ChangePasswordForm()

    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()

            flash("Your password has been successfully changed.")

            return redirect(url_for("main.index"))

        else:
            flash("Invalid password.")

    return render_template("auth/change_password.html", form=form)


@auth.route("/reset", methods=["GET", "POST"])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for("main.index"))

    form: FlaskForm = PasswordResetRequestForm()

    if form.validate_on_submit():
        user: User = User.query.filter_by(email=form.email.data.lower()).first()

        if user:
            token: str = user.generate_reset_token()
            send_email(
                user.email,
                "Reset your password",
                "auth/email/reset_password",
                user=user,
                token=token,
            )

        flash(
            "An email with instructions to reset your password \
has been sent to you."
        )

        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)


@auth.route("/reset/<token>", methods=["GET", "POST"])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for("main.index"))

    form: FlaskForm = PasswordResetForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash("Your password has been updated.")

            return redirect(url_for("auth.login"))
        else:
            flash("Your password has not been updated.")
            return redirect(url_for("main.index"))

    return render_template("auth/reset_password.html", form=form)


@auth.route("/change_email", methods=["GET", "POST"])
@login_required
def change_email_request():
    form: FlaskForm = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data.lower()
            token = current_user.generate_email_change_token(new_email)
            send_email(
                new_email,
                "Confirm your email address",
                "auth/email/change_email",
                user=current_user,
                token=token,
            )
            flash(
                "An email with instructions to confirm your new "
                "address has been sent to you."
            )

            return redirect(url_for("main.index"))

        else:
            flash("An invalid email address or password")

    return render_template("auth/change_email.html", form=form)


@auth.route("/change_email/<token>")
@login_required
def change_email(token) -> Response:
    if current_user.change_email(token):
        db.session.commit()
        flash("Your email address has been updated.")
    else:
        flash("Invalid request.")

    return redirect(url_for("main.index"))
