"""Scraper for SEC EDGAR Archive Directory listings.

Replaces the legacy `our_flash-light.py` script with:
- Full SEC EDGAR Fair Access compliance (custom `User-Agent` and rate limiting)
- Explicit structured parsing instead of fragile `.split('/')[3]` / `.split('/')[5][:-6]` indexing
- No silent `except IndexError: continue` failures — logs malformed entries with clear diagnostics
- Support for both legacy (`class="dir-entry2"` / nested path hrefs) and modern SEC EDGAR directory HTML tables
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd

from web_scraping.exceptions import ParsingError
from web_scraping.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

CIK_PATTERN = re.compile(r"(\d{1,10})")


class SecEdgarScraper(BaseScraper):
    """Extracts company/CIK directory entries from SEC EDGAR Archives."""

    def __init__(
        self,
        config=None,
        http_client=None,
        base_url: str | None = None,
    ) -> None:
        super().__init__(config=config, http_client=http_client)
        self.base_url = base_url or self.config.sec_edgar_base_url

    def _parse_entry_href(self, href: str, link_text: str) -> dict[str, str] | None:
        """Safely extracts CIK, Name, and absolute Link from an anchor tag.

        Supports both:
        1. Structured paths like `/Archives/edgar/data/0000320193/Apple_Inc/0000320193-index.html`
           or `/Archives/edgar/data/company_name/filing/cik_number.txt`
        2. Standard SEC directory links like `/Archives/edgar/data/320193` or `0000320193/`
        """
        href_clean = href.strip()
        if not href_clean or href_clean.startswith(("?", "#", "javascript:")):
            return None
        if href_clean in ("/", "../", "/Archives/edgar/"):
            return None

        segments = [seg.strip() for seg in href_clean.strip("/").split("/") if seg.strip()]
        if not segments:
            return None

        full_url = urljoin(self.base_url, href_clean)

        # Case 1: Legacy multi-segment path (e.g. /Archives/edgar/data/<Name>/<subpath>/<CIK>.index)
        if len(segments) >= 5 and segments[0] == "Archives" and segments[1] == "edgar":
            candidate_name = segments[3]
            raw_last = segments[4] if len(segments) == 5 else segments[5]
            cik_clean = re.sub(r"\.[a-zA-Z0-9]+$", "", raw_last)
            if cik_clean.endswith("-index"):
                cik_clean = cik_clean[:-6]
            return {
                "CIK": cik_clean.zfill(10) if cik_clean.isdigit() else cik_clean,
                "Name": link_text.strip() or candidate_name,
                "Link": full_url,
            }

        # Case 2: Standard SEC EDGAR directory listing (e.g. href="0000320193" or "/Archives/edgar/data/320193")
        last_segment = segments[-1]
        cik_match = CIK_PATTERN.fullmatch(last_segment)
        if cik_match:
            cik_digits = cik_match.group(1).zfill(10)
            display_name = link_text.strip()
            if not display_name or display_name == last_segment:
                display_name = f"CIK-{cik_digits}"
            return {
                "CIK": cik_digits,
                "Name": display_name,
                "Link": full_url,
            }

        return None

    def parse_html(self, html: str) -> pd.DataFrame:
        """Parses SEC EDGAR directory HTML into a structured DataFrame of CIKs, Names, and Links."""
        soup = BeautifulSoup(html, "html.parser")

        # First look for explicit `a.dir-entry2` links, falling back to table/directory links
        anchors = soup.find_all("a", class_="dir-entry2")
        if not anchors:
            anchors = soup.select("table a[href], #main-content a[href], body a[href]")

        if not anchors:
            raise ParsingError("No directory anchor (<a>) elements found on SEC EDGAR page.", url=self.base_url)

        records: list[dict[str, str]] = []
        skipped_count = 0

        for anchor in anchors:
            href = anchor.get("href")
            if not href or not isinstance(href, str):
                continue

            parsed = self._parse_entry_href(href, anchor.get_text())
            if parsed is None:
                skipped_count += 1
                logger.debug("Skipped non-entity link href=%r", href)
                continue

            records.append(parsed)

        if not records:
            raise ParsingError(
                f"No valid SEC EDGAR company entries could be parsed from {len(anchors)} links "
                f"(skipped {skipped_count} non-matching links).",
                url=self.base_url,
            )

        df = pd.DataFrame.from_records(records, columns=["CIK", "Name", "Link"])
        df = df.drop_duplicates(subset=["CIK", "Link"], keep="first").reset_index(drop=True)
        return df

    def scrape(self) -> pd.DataFrame:
        """Fetches the SEC EDGAR directory listing and returns a cleaned DataFrame."""
        logger.info("Scraping SEC EDGAR directory from %s", self.base_url)
        html = self.http_client.get_text(self.base_url)
        df = self.parse_html(html)
        logger.info("Successfully extracted %d SEC EDGAR records.", len(df))
        return df
