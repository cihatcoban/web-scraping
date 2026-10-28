"""Scraper for Wikipedia company tables (supporting English, Turkish, and multilingual pages)."""

from __future__ import annotations

import logging
import re
from bs4 import BeautifulSoup, Tag
import pandas as pd

from web_scraping.exceptions import ParsingError
from web_scraping.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

FOOTNOTE_PATTERN = re.compile(r"\[[0-9a-zA-Z\s]+\]")

RANK_KEYWORDS = {"rank", "sıra", "no", "#", "sira"}
ENTITY_KEYWORDS = {"name", "company", "şirket", "sirket", "firm", "kurum", "işletme", "isletme"}
METRIC_KEYWORDS = {"revenue", "gelir", "sales", "ciro", "turnover", "employees", "çalışanlar", "calisanlar"}


def clean_cell_text(raw_text: str) -> str:
    """Strips citation brackets and extra whitespace."""
    cleaned = FOOTNOTE_PATTERN.sub("", raw_text)
    cleaned = re.sub(r"\[.*?\]", "", cleaned)
    return " ".join(cleaned.split())


class WikipediaCompaniesScraper(BaseScraper):
    """Extracts and cleans company ranking tables from Wikipedia articles."""

    def __init__(
        self,
        config=None,
        http_client=None,
        url: str | None = None,
        table_index: int | None = None,
        clean_numbers: bool = False,
    ) -> None:
        super().__init__(config=config, http_client=http_client)
        self.url = url or self.config.wikipedia_companies_url
        self.table_index = table_index
        self.clean_numbers = clean_numbers

    def _score_table(self, table: Tag) -> tuple[int, int]:
        rows = table.find_all("tr")
        if not rows:
            return (-1, 0)

        header_cells = rows[0].find_all(["th", "td"])
        header_texts = [clean_cell_text(c.get_text()).lower() for c in header_cells]

        score = 0
        if any(any(k in h for k in RANK_KEYWORDS) for h in header_texts):
            score += 3
        if any(any(k in h for k in ENTITY_KEYWORDS) for h in header_texts):
            score += 3
        if any(any(k in h for k in METRIC_KEYWORDS) for h in header_texts):
            score += 2

        if len(header_texts) <= 2 and any("açıklama" in h or "description" in h for h in header_texts):
            score -= 5

        return (score, len(rows))

    def _locate_target_table(self, soup: BeautifulSoup) -> Tag:
        candidate_tables = soup.find_all("table", class_="wikitable")
        if not candidate_tables:
            candidate_tables = soup.find_all("table")

        if not candidate_tables:
            raise ParsingError("No HTML <table> elements found on page.", url=self.url)

        if self.table_index is not None:
            if 0 <= self.table_index < len(candidate_tables):
                return candidate_tables[self.table_index]
            raise ParsingError(
                f"Requested table_index={self.table_index}, but only "
                f"{len(candidate_tables)} tables were found.",
                url=self.url,
            )

        scored_tables = []
        for idx, table in enumerate(candidate_tables):
            score, row_count = self._score_table(table)
            scored_tables.append((score, row_count, idx, table))

        scored_tables.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return scored_tables[0][3]

    def parse_html(self, html: str) -> pd.DataFrame:
        soup = BeautifulSoup(html, "html.parser")
        table = self._locate_target_table(soup)

        rows = table.find_all("tr")
        if not rows:
            raise ParsingError("Target table contains no <tr> rows.", url=self.url)

        headers: list[str] = []
        header_row_idx = 0
        for idx, row in enumerate(rows[:3]):
            th_cells = row.find_all("th")
            if th_cells:
                headers = [clean_cell_text(th.get_text()) for th in th_cells]
                header_row_idx = idx
                break

        if not headers:
            headers = [clean_cell_text(th.get_text()) for th in table.find_all("th")]

        if not headers:
            raise ParsingError("Could not extract table column headers (<th>).", url=self.url)

        unique_headers = []
        header_counts: dict[str, int] = {}
        for h in headers:
            label = h if h else "Column"
            if label in header_counts:
                header_counts[label] += 1
                unique_headers.append(f"{label}_{header_counts[label]}")
            else:
                header_counts[label] = 1
                unique_headers.append(label)
        headers = unique_headers

        records: list[dict[str, str]] = []
        skipped_rows = 0

        for row_idx, row in enumerate(rows[header_row_idx + 1:], start=header_row_idx + 1):
            cells = row.find_all(["td", "th"])
            if not cells:
                continue

            if not row.find_all("td"):
                continue

            values = [clean_cell_text(cell.get_text()) for cell in cells]

            if len(values) != len(headers):
                if len(values) == len(headers) - 1:
                    values.append("")
                elif len(values) > len(headers):
                    values = values[:len(headers)]
                else:
                    skipped_rows += 1
                    continue

            record = dict(zip(headers, values))
            records.append(record)

        if not records:
            raise ParsingError(
                f"No valid data rows extracted from table (skipped {skipped_rows} rows).",
                url=self.url,
            )

        df = pd.DataFrame.from_records(records, columns=headers)
        df = df.drop_duplicates().reset_index(drop=True)

        if self.clean_numbers:
            df = self._normalize_numeric_columns(df)

        return df

    @staticmethod
    def _normalize_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        def clean_val(series: pd.Series) -> pd.Series:
            return (
                series.astype(str)
                .str.replace("$", "", regex=False)
                .str.replace("€", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.replace("−", "-", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )

        for col in df.columns:
            col_lower = col.lower()
            if any(k in col_lower for k in ["rank", "sıra", "sira"]):
                df[col] = pd.to_numeric(clean_val(df[col]), errors="coerce")
            elif any(k in col_lower for k in ["revenue", "gelir", "sales", "ciro", "employees", "çalışanlar", "calisanlar"]):
                cleaned = clean_val(df[col])
                df[col] = pd.to_numeric(cleaned, errors="coerce")

        return df

    def scrape(self) -> pd.DataFrame:
        logger.info("Scraping Wikipedia table from %s", self.url)
        html = self.http_client.get_text(self.url)
        df = self.parse_html(html)
        logger.info("Successfully extracted %d company records.", len(df))
        return df