class IDriveException(Exception):
    """A base class for all I Drive exceptions."""

class HttpError(IDriveException):
    """
    Base class for all HTTP errors.
    Provides helpers to inspect the underlying response.
    """

    def __init__(self, response, message=None):
        self.response = response
        self.status = getattr(response, "status_code", None)
        self.headers = getattr(response, "headers", {})
        self.text = getattr(response, "text", "")
        self.content = getattr(response, "content", b"")

        if message is None:
            message = f"HTTP {self.status}: {self.text}"

        super().__init__(message)

    def json(self):
        """Return JSON body or None if invalid."""
        try:
            return self.response.json()
        except Exception:
            return None

    def header(self, key, default=None):
        """Safely get a header value."""
        return self.headers.get(key, default)


class BadRequestError(HttpError):
    """Raised when 400"""


class UnauthorizedError(HttpError):
    """Raised when 401"""


class ResourcePermissionError(HttpError):
    """Raised when 403"""


class ResourceNotFoundError(HttpError):
    """Raised when 404"""


class BadMethodError(HttpError):
    """Raised when 405"""


class MissingOrIncorrectResourcePasswordError(HttpError):
    """Raised when 469"""


class InternalServerError(HttpError):
    """Raised when 500"""


class RateLimitError(HttpError):
    """Raised when 429"""

    def __init__(self, response):
        # Extract wait time ONLY from the Retry-After header
        header_wait = response.headers.get("Retry-After")

        if header_wait and header_wait.isdigit():
            self.wait = int(header_wait)
        else:
            self.wait = 2.0

        msg = (
            f"Rate limited (HTTP 429). Retry after {self.wait} seconds."
            if self.wait is not None
            else f"Rate limited (HTTP 429). Retry-After header missing. Fallback to {self.wait}"
        )

        super().__init__(response, message=msg)


class ServiceUnavailableError(HttpError):
    """Raised when 503"""
    def __init__(self, response):
        self.wait = 2.0
        super().__init__(response)


class ForcedLogoutException(IDriveException):
    """Raised when your session is invalidated, and you're forced to re login"""
