"""Resilient HTTP client with retries, timeouts, rate limiting, and BeautifulSoup integration."""

from __future__ import annotations

import logging
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

from web_scraping.config import ScraperConfig
from web_scraping.exceptions import NetworkError

logger = logging.getLogger(__name__)


class HttpClient:
    """Wrapper around requests.Session providing retry logic and rate limiting."""

    def __init__(self, config: ScraperConfig | None = None) -> None:
        self.config = config or ScraperConfig.from_env()
        self.session = self._build_session()
        self._last_request_ts: float = 0.0

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self.config.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )
        retry_strategy = Retry(
            total=self.config.max_retries,
            connect=self.config.max_retries,
            read=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _respect_rate_limit(self) -> None:
        if self.config.rate_limit_delay <= 0:
            return
        elapsed = time.monotonic() - self._last_request_ts
        remaining = self.config.rate_limit_delay - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def get_text(self, url: str) -> str:
        """Fetches URL content as decoded text, raising NetworkError on failure."""
        self._respect_rate_limit()
        logger.debug("Fetching URL: %s", url)
        try:
            response = self.session.get(url, timeout=self.config.timeout_seconds)
            self._last_request_ts = time.monotonic()
        except requests.RequestException as exc:
            raise NetworkError(
                f"Failed to fetch {url}: {exc}", url=url
            ) from exc

        if response.status_code >= 400:
            raise NetworkError(
                f"HTTP {response.status_code} returned for {url}. "
                "Verify URL and SCRAPER_USER_AGENT compliance.",
                url=url,
                status_code=response.status_code,
            )
        return response.text

    def get_soup(self, url: str, parser: str = "html.parser") -> BeautifulSoup:
        """Fetches URL and parses it into a BeautifulSoup DOM tree."""
        html = self.get_text(url)
        return BeautifulSoup(html, parser)

    def close(self) -> None:
        """Closes underlying HTTP session connections."""
        self.session.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
