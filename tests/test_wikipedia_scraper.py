"""Unit tests for WikipediaCompaniesScraper HTML parsing, deduplication, and numeric cleaning."""

import unittest

from web_scraping.exceptions import ParsingError
from web_scraping.scrapers.wikipedia import WikipediaCompaniesScraper, clean_cell_text

SAMPLE_WIKIPEDIA_HTML = """
<!DOCTYPE html>
<html>
<body>
  <table class="wikitable">
    <tr><th>Notice</th></tr>
    <tr><td>Metadata table that should be ignored</td></tr>
  </table>
  <table class="wikitable sortable">
    <tr>
      <th>Rank</th>
      <th>Name</th>
      <th>Industry</th>
      <th>Revenue (USD millions)</th>
      <th>Revenue growth</th>
      <th>Employees</th>
      <th>Headquarters</th>
    </tr>
    <tr>
      <td>1</td>
      <td>Walmart</td>
      <td>Retail</td>
      <td>611,289</td>
      <td>6.7%</td>
      <td>2,100,000</td>
      <td>Bentonville, Arkansas</td>
    </tr>
    <tr>
      <td>61</td>
      <td>StoneX Group</td>
      <td>Financials</td>
      <td>66,036</td>
      <td>55.3%</td>
      <td>4,000[2]</td>
      <td>New York City, New York</td>
    </tr>
    <!-- Duplicate row to verify automatic deduplication -->
    <tr>
      <td>1</td>
      <td>Walmart</td>
      <td>Retail</td>
      <td>611,289</td>
      <td>6.7%</td>
      <td>2,100,000</td>
      <td>Bentonville, Arkansas</td>
    </tr>
  </table>
</body>
</html>
"""


class TestWikipediaCompaniesScraper(unittest.TestCase):
    def test_clean_cell_text_removes_footnotes_and_extra_spaces(self) -> None:
        self.assertEqual(clean_cell_text("  4,000[2]   "), "4,000")
        self.assertEqual(clean_cell_text("Berkshire Hathaway[a][12]"), "Berkshire Hathaway")

    def test_parse_html_selects_correct_table_and_deduplicates(self) -> None:
        scraper = WikipediaCompaniesScraper(clean_numbers=False)
        df = scraper.parse_html(SAMPLE_WIKIPEDIA_HTML)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df["Name"]), ["Walmart", "StoneX Group"])
        self.assertEqual(df.loc[1, "Employees"], "4,000")

    def test_parse_html_with_clean_numbers_converts_types(self) -> None:
        scraper = WikipediaCompaniesScraper(clean_numbers=True)
        df = scraper.parse_html(SAMPLE_WIKIPEDIA_HTML)
        self.assertEqual(df.loc[0, "Rank"], 1)
        self.assertEqual(df.loc[0, "Revenue (USD millions)"], 611289)
        self.assertAlmostEqual(df.loc[0, "Revenue growth (%)"], 6.7)
        self.assertEqual(df.loc[1, "Employees"], 4000)

    def test_parse_html_raises_parsing_error_when_no_tables(self) -> None:
        scraper = WikipediaCompaniesScraper()
        with self.assertRaises(ParsingError):
            scraper.parse_html("<html><body><p>No tables here</p></body></html>")


if __name__ == "__main__":
    unittest.main()
