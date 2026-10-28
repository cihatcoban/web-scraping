"""Command-line interface for running scrapers and exporting datasets."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from web_scraping.config import ScraperConfig
from web_scraping.exceptions import ScraperError
from web_scraping.http_client import HttpClient
from web_scraping.scrapers.generic import GenericScraper
from web_scraping.scrapers.sec_edgar import SecEdgarScraper
from web_scraping.scrapers.wikipedia import WikipediaCompaniesScraper


def configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="web-scraper",
        description="Resilient Web Scraping Toolkit (Wikipedia, SEC EDGAR & Universal Generic Scraper)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override output directory for exported CSV files (default: from .env or 'data/').",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Override logging verbosity.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Wikipedia subcommand
    wiki_parser = subparsers.add_parser(
        "wikipedia",
        help="Scrape company tables from Wikipedia.",
    )
    wiki_parser.add_argument("--url", type=str, default=None, help="Custom Wikipedia article URL.")
    wiki_parser.add_argument("--table-index", type=int, default=None, help="Table index.")
    wiki_parser.add_argument("--output", type=str, default="us_largest_companies_by_revenue.csv")
    wiki_parser.add_argument("--clean-numbers", action="store_true")

    # 2. SEC EDGAR subcommand
    sec_parser = subparsers.add_parser(
        "sec-edgar",
        help="Scrape company/CIK directory entries from SEC EDGAR Archives.",
    )
    sec_parser.add_argument("--url", type=str, default=None, help="Custom SEC EDGAR base URL.")
    sec_parser.add_argument("--output", type=str, default="sec_edgar_companies.csv")

    # 3. Generic universal subcommand
    generic_parser = subparsers.add_parser(
        "generic",
        help="Scrape ANY website, HTML table, custom CSS selector, JSON API, or XML feed.",
    )
    generic_parser.add_argument("--url", type=str, required=True, help="Target URL.")
    generic_parser.add_argument("--selector", type=str, default=None, help="Optional CSS selector.")
    generic_parser.add_argument("--table-index", type=int, default=None, help="0-based table index.")
    generic_parser.add_argument("--output", type=str, default="extracted_data.csv")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        base_config = ScraperConfig.from_env()
        config = ScraperConfig(
            user_agent=base_config.user_agent,
            timeout_seconds=base_config.timeout_seconds,
            max_retries=base_config.max_retries,
            backoff_factor=base_config.backoff_factor,
            rate_limit_delay=base_config.rate_limit_delay,
            output_dir=args.output_dir or base_config.output_dir,
            log_level=args.log_level or base_config.log_level,
            wikipedia_companies_url=base_config.wikipedia_companies_url,
            sec_edgar_base_url=base_config.sec_edgar_base_url,
        )
        configure_logging(config.log_level)

        with HttpClient(config) as client:
            if args.command == "wikipedia":
                scraper = WikipediaCompaniesScraper(
                    config=config,
                    http_client=client,
                    url=args.url,
                    table_index=args.table_index,
                    clean_numbers=args.clean_numbers,
                )
                df = scraper.scrape()
                output_path = scraper.export_csv(df, args.output)
                print(f"Scraped {len(df)} companies -> {output_path}")
                return 0

            if args.command == "sec-edgar":
                scraper = SecEdgarScraper(
                    config=config,
                    http_client=client,
                    base_url=args.url,
                )
                df = scraper.scrape()
                output_path = scraper.export_csv(df, args.output)
                print(f"Scraped {len(df)} SEC EDGAR entries -> {output_path}")
                return 0

            if args.command == "generic":
                scraper = GenericScraper(
                    config=config,
                    http_client=client,
                    url=args.url,
                    selector=args.selector,
                    table_index=args.table_index,
                )
                df = scraper.scrape()
                output_path = scraper.export_csv(df, args.output)
                print(f"Scraped {len(df)} records from {args.url} -> {output_path}")
                return 0

    except ScraperError as exc:
        logging.getLogger(__name__).error("Scraping failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())