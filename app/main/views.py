"""The Blueprint's custom routes."""
from typing import Any

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from . import main
from .forms import EditProfileAdminForm, EditProfileForm, PostForm
from .. import db
from ..decorators import admin_required
from ..models import Permission, Post, Role, User


@main.route("/", methods=["GET", "POST"])
def index() -> Any:
    # form = NameForm()
    # if form.validate_on_submit():
    #     user = User.query.filter_by(username=form.name.data).first()
    #     if user is None:
    #         user = User(username=form.name.data)
    #         db.session.add(user)
    #         db.session.commit()
    #         session["known"] = False

    #         if current_app.config["FLASKY_ADMIN"]:
    #             send_email(
    #                 current_app.config["FLASKY_ADMIN"],
    #                 "New User",
    #                 "mail/new_user",
    #                 user=user,
    #             )

    #     else:
    #         session["known"] = True

    #     session["name"] = form.name.data
    #     form.name.data = ""
    #     return redirect(url_for(".index"))

    # return render_template(
    #     "index.html",
    #     form=form,
    #     name=session.get("name"),
    #     known=session.get("known", False),
    #     current_time=datetime.utcnow(),
    # )
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()

        return redirect(url_for(".index"))

    posts = Post.query.order_by(Post.timestamp.desc()).all()

    return render_template("index.html", form=form, posts=posts)


@main.route("/user/<username>")
def user(username: str) -> Any:
    user: Any = User.query.filter_by(username=username).first_or_404()

    posts = user.posts.order_by(Post.timestamp.desc()).all()

    return render_template("user.html", user=user, posts=posts)


@main.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data

        db.session.add(current_user._get_current_object())
        db.session.commit()

        flash("Your profile has been updated.")

        return redirect(url_for(".user", username=current_user.username))

    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me

    return render_template("edit_profile.html", form=form)


@main.route("/edit-profile/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_profile_admin(id: int) -> Any:
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data

        db.session.add(user)
        db.session.commit()

        flash("The profile has been updated")

        return redirect(url_for(".user", username=user.username))

    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me

    return render_template("edit_profile.html", form=form, user=user)
