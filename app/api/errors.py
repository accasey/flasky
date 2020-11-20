"""Specific error handling for the api blueprint."""
from typing import Any

from app.exceptions import ValidationError
from flask import jsonify

from . import api


def bad_request(message) -> Any:
    response = jsonify({"error": "bad request", "message": message})
    response.status_code = 400
    return response


def unauthorised(message) -> Any:
    response = jsonify({"error": "unauthorized", "message": message})
    response.status_code = 401
    return response


def forbidden(message) -> Any:
    response = jsonify({"error": "forbidden", "message": message})
    response.status_code = 403
    return response


@api.errorhandler(ValidationError)
def validation_error(e) -> Any:
    return bad_request(e.args[0])
