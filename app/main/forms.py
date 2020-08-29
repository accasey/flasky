"""The name form."""

import flask_wtf
import wtforms


class NameForm(flask_wtf.FlaskForm):
    """The name form class.

    Args:
        flask_wtf (FlaskForm): The form.
    """

    name = wtforms.StringField(
        "What is your name?", validators=[wtforms.validators.DataRequired()]
    )
    submit = wtforms.SubmitField("Submit")
