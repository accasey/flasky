"""The data models for the application."""
from datetime import datetime
import hashlib
from typing import Any

import bleach
from flask import current_app, request
from flask_login import UserMixin
from flask_login.mixins import AnonymousUserMixin
from itsdangerous import (
    BadSignature,
    SignatureExpired,
    TimedJSONWebSignatureSerializer as Serializer,
)
from markdown import markdown
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from . import login_manager


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)

    users = db.relationship("User", backref="role", lazy="dynamic")

    def add_permission(self, perm: int):
        if not self.has_permissions(perm):
            self.permissions += perm

    def remove_permission(self, perm: int):
        if self.has_permissions(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permissions(self, perm: int):
        return self.permissions & perm == perm

    @staticmethod
    def insert_roles():
        roles = {
            "User": [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            "Moderator": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE,
            ],
            "Administrator": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE,
                Permission.ADMIN,
            ],
        }
        default_role = "User"

        for r in roles:
            role = Role.query.filter_by(name=r).first()

            if role is None:
                role = Role(name=r)

            role.reset_permissions()

            for perm in roles[r]:
                role.add_permission(perm)

            role.default = role.name == default_role

            db.session.add(role)

        db.session.commit()

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def __repr__(self):
        return f"<Role {self.name} | id: {self.id} >"


class Follow(db.Model):
    __tablename__ = "follows"
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))

    posts = db.relationship("Post", backref="author", lazy="dynamic")

    followed = db.relationship(
        "Follow",
        foreign_keys=[Follow.follower_id],
        backref=db.backref("follower", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    followers = db.relationship(
        "Follow",
        foreign_keys=[Follow.followed_id],
        backref=db.backref("followed", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(
            Follow.follower_id == self.id
        )

    @property
    def password(self):
        raise AttributeError("password is not a readable attribue")

    @password.setter
    def password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # CONFIRMATION METHODS
    def generate_confirmation_token(self, expiration: int = 3600) -> str:
        s: Serializer = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({"confirm": self.id}).decode("utf-8")

    def confirm(self, token: str) -> bool:
        s: Serializer = Serializer(current_app.config["SECRET_KEY"])
        try:
            data: Any = s.loads(token.encode("utf-8"))
        except (BadSignature, SignatureExpired):
            return False

        if data.get("confirm") != self.id:
            return False

        self.confirmed = True
        db.session.add(self)

        return True

    # RESET PASSWORD METHODS
    def generate_reset_token(self, expiration: int = 3600) -> str:
        s: Serializer = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({"reset": self.id}).decode("utf-8")

    @staticmethod
    def reset_password(token: str, new_password: str) -> bool:
        s: Serializer = Serializer(current_app.config["SECRET_KEY"])

        try:
            data: Any = s.loads(token.encode("utf-8"))
        except (BadSignature, SignatureExpired):
            return False

        # query by the id passed in with token
        user: User = User.query.get(data.get("reset"))
        if user is None:
            return False

        user.password = new_password
        db.session.add(user)

        return True

    # EMAIL METHODS
    def generate_email_change_token(
        self, new_email: str, expiration: int = 3600
    ) -> str:
        s: Serializer = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({"change_email": self.id, "new_email": new_email}).decode(
            "utf-8"
        )

    def change_email(self, token: str) -> bool:
        s: Serializer = Serializer(current_app.config["SECRET_KEY"])

        try:
            data: Any = s.loads(token.encode("utf-8"))
        except (BadSignature, SignatureExpired):
            return False

        if data.get("change_email") != self.id:
            return False

        new_email = data.get("new_email")
        if new_email is None:
            return False

        if self.query.filter_by(email=new_email).first() is not None:
            return False

        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)

        return True

    # PERMISSIONS METHODS
    def can(self, perm: int) -> bool:
        return self.role is not None and self.role.has_permissions(perm)

    def is_administrator(self) -> bool:
        return self.can(Permission.ADMIN)

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def __repr__(self) -> str:
        return f"<User {self.username} | role_id: {self.role_id} | role: {self.role}>"

    def __init__(self, **kwargs) -> None:
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config["FLASKY_ADMIN"]:
                self.role = Role.query.filter_by(name="Administrator").first()

            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

        self.follow(self)

    def gravatar_hash(self) -> str:
        return hashlib.md5(self.email.lower().encode("utf-8")).hexdigest()  # noqa

    def gravatar(self, size=100, default="identicon", rating="g"):
        if request.is_secure:
            url = "https://secure.gravatar.com/avatar"
        else:
            url = "http://www.gravatar.com/avatar"

        hash = self.avatar_hash or self.gravatar_hash()

        return f"{url}/{hash}?s={size}&d={default}&r={rating}"

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        if user.id is None:
            return False

        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False

        return self.followers.filter_by(follower_id=user.id).first() is not None


class AnonymousUser(AnonymousUserMixin):
    def can(self, perm: int) -> bool:
        return False

    def is_administrator(self) -> bool:
        return False


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = [
            "a",
            "abbr",
            "acronym",
            "b",
            "blockquote",
            "code",
            "em",
            "i",
            "li",
            "ol",
            "pre",
            "strong",
            "ul",
            "h1",
            "h2",
            "h3",
            "p",
        ]
        target.body_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format="html"), tags=allowed_tags, strip=True
            )
        )


db.event.listen(Post.body, "set", Post.on_changed_body)


@login_manager.user_loader
def load_user(user_id: str) -> User:
    return User.query.get(int(user_id))


login_manager.anonymous_user = AnonymousUser
