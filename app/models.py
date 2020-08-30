"""The data models for the application."""
from typing import Any

from flask import current_app
from flask_login import UserMixin
from itsdangerous import (
    BadSignature,
    SignatureExpired,
    TimedJSONWebSignatureSerializer as Serializer,
)
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from . import login_manager


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    users = db.relationship("User", backref="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    confirmed = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        raise AttributeError("password is not a readable attribue")

    @password.setter
    def password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

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
            data: any = s.loads(token.encode("utf-8"))
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
        db.session.add(self)

        return True

    def __repr__(self):
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id: str) -> User:
    return User.query.get(int(user_id))
