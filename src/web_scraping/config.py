"""Environment-backed configuration with startup validation."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from web_scraping.exceptions import ConfigurationError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional if environment variables are set directly
    pass

DEFAULT_USER_AGENT = (
    "WebScrapingToolkit/1.0 "
    "(+https://github.com/cihatcoban/web-scraping; cihatcoban12@gmail.com)"
)
DEFAULT_WIKIPEDIA_URL = (
    "https://en.wikipedia.org/wiki/List_of_largest_companies_in_the_United_States_by_revenue"
)
DEFAULT_SEC_EDGAR_URL = "https://www.sec.gov/Archives/edgar/data/"


@dataclass(frozen=True)
class ScraperConfig:
    """Immutable configuration container validated at creation time."""

    user_agent: str = DEFAULT_USER_AGENT
    timeout_seconds: float = 15.0
    max_retries: int = 3
    backoff_factor: float = 1.0
    rate_limit_delay: float = 0.2
    output_dir: Path = Path("data")
    log_level: str = "INFO"
    wikipedia_companies_url: str = DEFAULT_WIKIPEDIA_URL
    sec_edgar_base_url: str = DEFAULT_SEC_EDGAR_URL

    def __post_init__(self) -> None:
        if not self.user_agent or not self.user_agent.strip():
            raise ConfigurationError(
                "SCRAPER_USER_AGENT must not be empty. Both Wikipedia and SEC EDGAR "
                "require a descriptive User-Agent header."
            )
        if self.timeout_seconds <= 0:
            raise ConfigurationError(
                f"SCRAPER_TIMEOUT_SECONDS must be positive, got {self.timeout_seconds}."
            )
        if self.max_retries < 0:
            raise ConfigurationError(
                f"SCRAPER_MAX_RETRIES must be >= 0, got {self.max_retries}."
            )
        if self.backoff_factor < 0:
            raise ConfigurationError(
                f"SCRAPER_BACKOFF_FACTOR must be >= 0, got {self.backoff_factor}."
            )
        if self.rate_limit_delay < 0:
            raise ConfigurationError(
                f"SCRAPER_RATE_LIMIT_DELAY must be >= 0, got {self.rate_limit_delay}."
            )

    @classmethod
    def from_env(cls) -> ScraperConfig:
        """Loads configuration from environment variables with sensible defaults."""
        try:
            timeout = float(os.getenv("SCRAPER_TIMEOUT_SECONDS", "15.0"))
            max_retries = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
            backoff = float(os.getenv("SCRAPER_BACKOFF_FACTOR", "1.0"))
            delay = float(os.getenv("SCRAPER_RATE_LIMIT_DELAY", "0.2"))
        except ValueError as exc:
            raise ConfigurationError(
                f"Invalid numeric value in environment variables: {exc}"
            ) from exc

        return cls(
            user_agent=os.getenv("SCRAPER_USER_AGENT", DEFAULT_USER_AGENT).strip(),
            timeout_seconds=timeout,
            max_retries=max_retries,
            backoff_factor=backoff,
            rate_limit_delay=delay,
            output_dir=Path(os.getenv("SCRAPER_OUTPUT_DIR", "data")),
            log_level=os.getenv("SCRAPER_LOG_LEVEL", "INFO").upper(),
            wikipedia_companies_url=os.getenv(
                "WIKIPEDIA_COMPANIES_URL", DEFAULT_WIKIPEDIA_URL
            ).strip(),
            sec_edgar_base_url=os.getenv(
                "SEC_EDGAR_BASE_URL", DEFAULT_SEC_EDGAR_URL
            ).strip(),
        )
