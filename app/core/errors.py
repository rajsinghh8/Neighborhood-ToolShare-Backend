"""Domain exception hierarchy. The base handler turns these into the error envelope."""
from __future__ import annotations


class AppError(Exception):
    """Base for every error deliberately raised by the application."""

    status_code = 500
    error = "Internal Server Error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.error)
        self.message = message or self.error


class BadRequestError(AppError):
    status_code = 400
    error = "Bad Request"


class UnauthorizedError(AppError):
    status_code = 401
    error = "Unauthorized"


class NotFoundError(AppError):
    status_code = 404
    error = "Not Found"


class ConflictError(AppError):
    status_code = 409
    error = "Conflict"


class ValidationFailedError(AppError):
    """Payload/query failed validation (422)."""

    status_code = 422
    error = "Unprocessable Entity"


class BusinessRuleError(ValidationFailedError):
    """A domain rule rejected otherwise well-formed input (also 422)."""
