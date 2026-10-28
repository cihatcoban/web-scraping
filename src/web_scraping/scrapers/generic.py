"""General-purpose resilient web scraper for arbitrary websites and data formats.

Supports:
1. HTML Tables (`<table>`): Automatically locates and parses the largest or user-selected table on any webpage.
2. Custom CSS Selectors: Extracts structured rows/cards using `--selector` (e.g. `table.ranking`, `.currency-card`).
3. JSON API Endpoints: Automatically detects JSON responses and normalizes them into tabular DataFrames.
4. XML Endpoints: Detects and parses XML feeds (such as Central Bank exchange rates).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup, Tag
import pandas as pd

from web_scraping.exceptions import ParsingError
from web_scraping.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


def clean_text(raw_text: str) -> str:
    """Strips excessive whitespace, tabs, and newlines."""
    return " ".join(raw_text.split())


class GenericScraper(BaseScraper):
    """Universal scraper capable of extracting tabular data from HTML, JSON APIs, and XML."""

    def __init__(
        self,
        config=None,
        http_client=None,
        url: str = "",
        selector: str | None = None,
        table_index: int | None = None,
    ) -> None:
        super().__init__(config=config, http_client=http_client)
        if not url:
            raise ValueError("URL must be specified for GenericScraper.")
        self.url = url
        self.selector = selector
        self.table_index = table_index

    def _parse_json(self, raw_text: str) -> pd.DataFrame:
        """Parses JSON content into a normalized pandas DataFrame."""
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ParsingError(f"Failed to parse JSON response: {exc}", url=self.url) from exc

        if isinstance(data, list):
            return pd.json_normalize(data)
        if isinstance(data, dict):
            # If dictionary contains a list of records under a key like 'data', 'items', 'results'
            for key in ["data", "items", "results", "records", "currencies"]:
                if key in data and isinstance(data[key], list):
                    return pd.json_normalize(data[key])
            # Otherwise normalize single object
            return pd.json_normalize([data])

        raise ParsingError("JSON content is neither a list nor an object.", url=self.url)

    def _parse_xml(self, raw_text: str) -> pd.DataFrame:
        """Parses XML feeds (e.g. TCMB exchange rates) into a tabular DataFrame."""
        try:
            root = ET.fromstring(raw_text.encode("utf-8"))
        except ET.ParseError as exc:
            raise ParsingError(f"Failed to parse XML response: {exc}", url=self.url) from exc

        records: list[dict[str, Any]] = []
        for child in root:
            entry: dict[str, Any] = dict(child.attrib)
            for sub in child:
                tag_name = sub.tag
                text_val = clean_text(sub.text or "")
                entry[tag_name] = text_val
            if entry:
                records.append(entry)

        if not records:
            raise ParsingError("No repeated records found in XML structure.", url=self.url)

        return pd.DataFrame.from_records(records)

    def _parse_html_table(self, table: Tag) -> pd.DataFrame:
        """Extracts headers and rows from an HTML <table> element."""
        rows = table.find_all("tr")
        if not rows:
            raise ParsingError("Selected table contains no <tr> rows.", url=self.url)

        headers: list[str] = []
        header_row_idx = 0
        for idx, row in enumerate(rows[:3]):
            th_cells = row.find_all(["th", "td"])
            # If the row has <th> cells, use it as header row
            if row.find_all("th"):
                headers = [clean_text(c.get_text()) for c in th_cells]
                header_row_idx = idx
                break

        if not headers:
            # Generate generic column names
            first_row_cells = rows[0].find_all(["td", "th"])
            headers = [f"Col_{i+1}" for i in range(len(first_row_cells))]
            header_row_idx = -1

        # Deduplicate headers
        unique_headers = []
        counts: dict[str, int] = {}
        for h in headers:
            label = h if h else "Column"
            if label in counts:
                counts[label] += 1
                unique_headers.append(f"{label}_{counts[label]}")
            else:
                counts[label] = 1
                unique_headers.append(label)
        headers = unique_headers

        records: list[dict[str, str]] = []
        for row in rows[header_row_idx + 1:]:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            # If row is only <th> and matches header length, it's a repeated header
            if not row.find_all("td") and len(cells) == len(headers):
                continue

            values = [clean_text(c.get_text()) for c in cells]
            if len(values) < len(headers):
                values.extend([""] * (len(headers) - len(values)))
            elif len(values) > len(headers):
                values = values[:len(headers)]

            records.append(dict(zip(headers, values)))

        if not records:
            raise ParsingError("No valid rows could be extracted from the table.", url=self.url)

        return pd.DataFrame.from_records(records, columns=headers)

    def _parse_html_selector(self, soup: BeautifulSoup, selector: str) -> pd.DataFrame:
        """Extracts text elements matching a user-provided CSS selector."""
        elements = soup.select(selector)
        if not elements:
            raise ParsingError(f"No elements matched CSS selector: '{selector}'", url=self.url)

        # If the selector points to a table, parse as table
        if elements[0].name == "table":
            return self._parse_html_table(elements[0])

        records: list[dict[str, str]] = []
        for idx, el in enumerate(elements, start=1):
            text = clean_text(el.get_text())
            link = el.get("href") or (el.find("a")["href"] if el.find("a") and el.find("a").get("href") else "")
            records.append({"Index": str(idx), "Content": text, "Link": str(link)})

        return pd.DataFrame.from_records(records)

    def parse_content(self, raw_content: str) -> pd.DataFrame:
        """Auto-detects format (JSON, XML, HTML) and extracts data accordingly."""
        stripped = raw_content.strip()

        # 1. Check if response is JSON
        if stripped.startswith(("[", "{")) and stripped.endswith(("]", "}")):
            try:
                return self._parse_json(stripped)
            except ParsingError:
                pass

        # 2. Check if response is XML
        if stripped.startswith("<?xml") or (stripped.startswith("<") and "xml" in stripped[:100].lower()):
            try:
                return self._parse_xml(stripped)
            except ParsingError:
                pass

        # 3. Parse as HTML
        soup = BeautifulSoup(raw_content, "html.parser")

        # Case A: User provided custom CSS selector
        if self.selector:
            return self._parse_html_selector(soup, self.selector)

        # Case B: Search for <table> elements
        tables = soup.find_all("table")
        if not tables:
            raise ParsingError(
                "No HTML <table> elements found on this page. If data is in cards, lists, or divs, "
                "provide a CSS selector with `--selector '<css_selector>'`.",
                url=self.url,
            )

        if self.table_index is not None:
            if 0 <= self.table_index < len(tables):
                return self._parse_html_table(tables[self.table_index])
            raise ParsingError(
                f"Requested table_index={self.table_index}, but only {len(tables)} tables exist.",
                url=self.url,
            )

        # Auto-detect largest data table by row count
        tables_by_rows = sorted(tables, key=lambda t: len(t.find_all("tr")), reverse=True)
        selected_table = tables_by_rows[0]
        logger.info(
            "Auto-selected largest table with %d rows out of %d tables found.",
            len(selected_table.find_all("tr")),
            len(tables),
        )
        return self._parse_html_table(selected_table)

    def scrape(self) -> pd.DataFrame:
        """Fetches data from URL and extracts structured DataFrame."""
        logger.info("Fetching data from %s", self.url)
        content = self.http_client.get_text(self.url)
        df = self.parse_content(content)
        logger.info("Successfully extracted %d records.", len(df))
        return df