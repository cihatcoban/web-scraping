"""Unit tests for SecEdgarScraper supporting both legacy and modern SEC EDGAR HTML layouts."""

import unittest

from web_scraping.exceptions import ParsingError
from web_scraping.scrapers.sec_edgar import SecEdgarScraper

LEGACY_EDGAR_HTML = """
<html>
<body>
  <a class="dir-entry2" href="/Archives/edgar/data/Apple_Inc/0000320193/0000320193-index.html">Apple Inc</a>
  <a class="dir-entry2" href="/Archives/edgar/data/Microsoft_Corp/0000789019/0000789019-index.html">Microsoft Corp</a>
  <a class="dir-entry2" href="../">Parent Directory</a>
</body>
</html>
"""

MODERN_EDGAR_HTML = """
<html>
<body>
  <table>
    <tr><td><a href="/Archives/edgar/data/320193">0000320193</a></td></tr>
    <tr><td><a href="/Archives/edgar/data/789019">0000789019</a></td></tr>
  </table>
</body>
</html>
"""


class TestSecEdgarScraper(unittest.TestCase):
    def test_parse_legacy_dir_entry2_links(self) -> None:
        scraper = SecEdgarScraper()
        df = scraper.parse_html(LEGACY_EDGAR_HTML)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.loc[0, "CIK"], "0000320193")
        self.assertEqual(df.loc[0, "Name"], "Apple Inc")
        self.assertTrue(df.loc[0, "Link"].startswith("https://www.sec.gov/Archives/edgar/data/"))

    def test_parse_modern_sec_directory_table_links(self) -> None:
        scraper = SecEdgarScraper()
        df = scraper.parse_html(MODERN_EDGAR_HTML)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df["CIK"]), ["0000320193", "0000789019"])

    def test_parse_raises_parsing_error_on_empty_html(self) -> None:
        scraper = SecEdgarScraper()
        with self.assertRaises(ParsingError):
            scraper.parse_html("<html><body><div>No links</div></body></html>")


if __name__ == "__main__":
    unittest.main()
