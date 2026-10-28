"""Custom exception hierarchy for deterministic error handling (Keystone No-Silent-Failures standard)."""


class ScraperError(Exception):
    """Base exception for all errors raised by the web scraping toolkit."""


class ConfigurationError(ScraperError):
    """Raised when environment or runtime configuration is invalid or incomplete."""


class NetworkError(ScraperError):
    """Raised when an HTTP request fails after retries or times out."""

    def __init__(self, message: str, url: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.url = url
        self.status_code = status_code


class ParsingError(ScraperError):
    """Raised when expected HTML structures or table columns cannot be parsed."""

    def __init__(self, message: str, url: str | None = None) -> None:
        super().__init__(message)
        self.url = url
