"""Abstract base contract for all scrapers."""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from pathlib import Path
import pandas as pd

from web_scraping.config import ScraperConfig
from web_scraping.http_client import HttpClient

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Template method pattern for fetching, parsing, cleaning, and exporting datasets."""

    def __init__(
        self,
        config: ScraperConfig | None = None,
        http_client: HttpClient | None = None,
    ) -> None:
        self.config = config or ScraperConfig.from_env()
        self.http_client = http_client or HttpClient(self.config)

    @abstractmethod
    def scrape(self) -> pd.DataFrame:
        """Executes the scrape workflow and returns a cleaned pandas DataFrame."""

    def export_csv(self, df: pd.DataFrame, filename: str) -> Path:
        """Saves a DataFrame to CSV inside the configured output directory."""
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        target_path = output_dir / filename
        df.to_csv(target_path, index=False, encoding="utf-8")
        logger.info("Exported %d rows to %s", len(df), target_path)
        return target_path
