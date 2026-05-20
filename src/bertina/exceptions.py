class BertinaError(Exception):
    """Base exception for all bertina errors."""


class BertinaHTTPError(BertinaError):
    """Raised when the server returns a non-2xx response."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class BertinaRateLimitError(BertinaHTTPError):
    """Raised on HTTP 429 Too Many Requests."""

    def __init__(self) -> None:
        super().__init__("Rate limited by Bertina (HTTP 429)", status_code=429)


class BertinaParseError(BertinaError):
    """Raised when HTML parsing fails to extract expected data."""

    def __init__(self, message: str, url: str = "") -> None:
        super().__init__(message)
        self.url = url
