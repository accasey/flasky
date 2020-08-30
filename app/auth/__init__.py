"""The auth blueprint creation."""
from flask import Blueprint

auth = Blueprint("auth", __name__)

# Avoid circular dependencies
from . import views  # noqa
