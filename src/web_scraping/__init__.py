"""Web Scraping Toolkit — Modular, resilient data extraction package."""

from web_scraping.config import ScraperConfig
from web_scraping.exceptions import (
    ConfigurationError,
    NetworkError,
    ParsingError,
    ScraperError,
)
from web_scraping.http_client import HttpClient
from web_scraping.scrapers.sec_edgar import SecEdgarScraper
from web_scraping.scrapers.wikipedia import WikipediaCompaniesScraper

__all__ = [
    "ScraperConfig",
    "ScraperError",
    "ConfigurationError",
    "NetworkError",
    "ParsingError",
    "HttpClient",
    "WikipediaCompaniesScraper",
    "SecEdgarScraper",
]

__version__ = "1.0.0"
