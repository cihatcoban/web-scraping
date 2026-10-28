"""Scraper implementations for structured data extraction."""

from web_scraping.scrapers.base import BaseScraper
from web_scraping.scrapers.sec_edgar import SecEdgarScraper
from web_scraping.scrapers.wikipedia import WikipediaCompaniesScraper

__all__ = [
    "BaseScraper",
    "WikipediaCompaniesScraper",
    "SecEdgarScraper",
]
