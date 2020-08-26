from datetime import datetime
import os
from typing import Tuple

from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
import flask_wtf
import wtforms

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_APP_KEY")
bootstrap = Bootstrap(app)
moment = Moment(app)


class NameForm(flask_wtf.FlaskForm):
    name = wtforms.StringField(
        "What is your name?", validators=[wtforms.validators.DataRequired()]
    )
    submit = wtforms.SubmitField("Submit")


@app.route("/")
def index():
    # return "<h1>Hello World</h1>"
    # user_agent = request.headers.get("User-Agent")
    # return f"<p>Your browser is {user_agent}</p>"
    return render_template("index.html", current_time=datetime.utcnow())


@app.route("/user/<string:name>")
def user(name):
    return render_template("user.html", name=name)


@app.errorhandler(404)
def page_not_found(e) -> Tuple:
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e) -> Tuple:
    return render_template("500.html"), 500


if __name__ == "__main__":
    # app.run(debug=True)
    app.run()
