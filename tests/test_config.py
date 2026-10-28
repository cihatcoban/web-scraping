"""Unit tests for ScraperConfig startup validation."""

import os
import unittest
from unittest.mock import patch

from web_scraping.config import ScraperConfig
from web_scraping.exceptions import ConfigurationError


class TestScraperConfig(unittest.TestCase):
    def test_default_config_is_valid(self) -> None:
        config = ScraperConfig()
        self.assertTrue(config.user_agent.startswith("WebScrapingToolkit"))
        self.assertEqual(config.timeout_seconds, 15.0)
        self.assertEqual(config.max_retries, 3)

    def test_empty_user_agent_raises_configuration_error(self) -> None:
        with self.assertRaises(ConfigurationError):
            ScraperConfig(user_agent="   ")

    def test_negative_timeout_raises_configuration_error(self) -> None:
        with self.assertRaises(ConfigurationError):
            ScraperConfig(timeout_seconds=0)

    def test_negative_retries_raises_configuration_error(self) -> None:
        with self.assertRaises(ConfigurationError):
            ScraperConfig(max_retries=-1)

    @patch.dict(
        os.environ,
        {
            "SCRAPER_USER_AGENT": "CustomAgent/2.0 (test@example.com)",
            "SCRAPER_TIMEOUT_SECONDS": "25.5",
            "SCRAPER_MAX_RETRIES": "5",
        },
        clear=False,
    )
    def test_from_env_reads_environment_variables(self) -> None:
        config = ScraperConfig.from_env()
        self.assertEqual(config.user_agent, "CustomAgent/2.0 (test@example.com)")
        self.assertEqual(config.timeout_seconds, 25.5)
        self.assertEqual(config.max_retries, 5)


if __name__ == "__main__":
    unittest.main()
