"""The main blueprint creation."""
from flask import Blueprint

main = Blueprint("main", __name__)

# Avoid circular dependencies
from . import errors, views  # noqa
from ..models import Permission  # noqa


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
