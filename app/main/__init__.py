"""The main blueprint creation."""
from flask import Blueprint

main = Blueprint("main", __name__)

# Avoid circular dependencies
from . import views, errors  # noqa
