from datetime import datetime
import os
from threading import Thread
from typing import Tuple

from flask import Flask, redirect, render_template, session, url_for
from flask_bootstrap import Bootstrap
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import flask_wtf
import wtforms

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_APP_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "data.sqlite"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["FLASKY_MAIL_SUBJECT_PREFIX"] = "[Flasky]"
app.config["FLASKY_MAIL_SENDER"] = "Flasky Admin <flasky@example.com>"
app.config["FLASKY_ADMIN"] = os.getenv("FLASKY_ADMIN")


bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)


class NameForm(flask_wtf.FlaskForm):
    name = wtforms.StringField(
        "What is your name?", validators=[wtforms.validators.DataRequired()]
    )
    submit = wtforms.SubmitField("Submit")


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    users = db.relationship("User", backref="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))

    def __repr__(self):
        return f"<User {self.username}>"


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    msg = Message(
        app.config["FLASKY_MAIL_SUBJECT_PREFIX"] + subject,
        sender=app.config["FLASKY_MAIL_SENDER"],
        recipients=[to],
    )
    msg.body = render_template(template + ".txt", **kwargs)
    msg.html = render_template(template + ".html", **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


@app.route("/", methods=["GET", "POST"])
def index():
    # return "<h1>Hello World</h1>"
    # user_agent = request.headers.get("User-Agent")
    # return f"<p>Your browser is {user_agent}</p>"
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session["known"] = False

            if app.config["FLASKY_ADMIN"]:
                send_email(
                    app.config["FLASKY_ADMIN"], "New User", "mail/new_user", user=user
                )

        else:
            session["known"] = True

        session["name"] = form.name.data
        form.name.data = ""

        return redirect(url_for("index"))

    return render_template(
        "index.html",
        form=form,
        name=session.get("name"),
        known=session.get("known", False),
        current_time=datetime.utcnow(),
    )


@app.route("/user/<string:name>")
def user(name):
    return render_template("user.html", name=name)


@app.errorhandler(404)
def page_not_found(e) -> Tuple:
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e) -> Tuple:
    return render_template("500.html"), 500


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


if __name__ == "__main__":
    # app.run(debug=True)
    app.run()
