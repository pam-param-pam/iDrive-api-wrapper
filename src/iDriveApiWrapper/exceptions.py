class IDriveException(Exception):
    """A base class for all I Drive exceptions."""


class BadRequestError(IDriveException):
    """Raised when 400"""


class UnauthorizedError(IDriveException):
    """Raised when 401"""


class ResourcePermissionError(IDriveException):
    """Raised when 403"""


class ResourceNotFoundError(IDriveException):
    """Raised when 404"""


class RateLimitException(IDriveException):
    """Raised when 429"""


class MissingOrIncorrectResourcePasswordError(IDriveException):
    """Raised when 469"""

class InternalServerError(IDriveException):
    """Raised when 500"""

class ServiceUnavailable(IDriveException):
    """Raised when 503"""
