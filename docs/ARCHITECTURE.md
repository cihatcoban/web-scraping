# Keystone Architecture & Engineering Audit (`docs/ARCHITECTURE.md`)

This document records the **Keystone Engineering Framework** from <a>https://github.com/cihatcoban/keystone</a> audit (`/review`, `/secure`, `/perf`, `/refactor`) performed on the legacy repository and the architectural decisions governing the modernized structure.

## 1. Multi-Lens Audit of Legacy Repository

| Lens | Legacy Issue Identified | Keystone Remediation |
| :--- | :--- | :--- |
| **Security & Hygiene (`/secure`)** | Committed entire Windows `venv/` directory (~100+ packages & `.exe` binaries) and `pyvenv.cfg` containing personal local filesystem paths. | Removed `venv/` completely; added comprehensive `.gitignore` and `.env.example` template. |
| **Compliance & Blocking (`/secure`)** | `requests.get(url)` sent default `python-requests` User-Agent with no rate limiting; SEC EDGAR (`sec.gov`) blocks requests without a custom `User-Agent` header (`403 Forbidden`). | Implemented `HttpClient` with configurable `SCRAPER_USER_AGENT`, exponential backoff retries, timeouts, and rate-limit delay. |
| **Silent Failures (`/debug`)** | `our_flash-light.py` caught `IndexError` with `except IndexError: continue`, silently returning an empty dataset when HTML link formats differed. | Introduced custom exceptions (`NetworkError`, `ParsingError`, `ConfigurationError`) and structured logging (`logging`). |
| **Performance & Data Quality (`/perf`)** | `web_scraping_table1.py` appended rows inside a loop via `df.loc[lenght] = ...` ($O(N^2)$ memory copies) and wrote duplicated rows (200 rows for 100 companies) into a misnamed file (`WorldPopulationData.csv`). | Replaced loop mutation with list-of-dicts `pd.DataFrame.from_records()`, stripped `[2]` footnote citations, deduplicated by `(Rank, Name)`, and renamed dataset to `sample_us_largest_companies.csv`. |
| **Repository Bloat (`/refactor`)** | `table_1_show.ipynb` stored ~550 KB of raw Wikipedia HTML inside Cell 2/3 stdout outputs. | Replaced with a clean, reproducible `notebooks/wikipedia_revenue_exploration.ipynb`. |

## 2. System Architecture & Module Boundaries

```text
web-scraping/
├── main.py                              # Zero-install CLI bootstrapper
├── pyproject.toml                       # PEP 621 package metadata & entrypoints
├── requirements.txt                     # Pinned runtime dependencies
├── .env.example                         # Environment variable template
├── .gitignore                           # Git hygiene rules
├── LICENSE                              # MIT License
├── CONTRIBUTING.md                      # Bilingual contributor & Keystone guide
├── README.md                            # Comprehensive project documentation
├── data/
│   └── sample_us_largest_companies.csv  # Cleaned, deduplicated Top 100 US Companies dataset
├── docs/
│   └── ARCHITECTURE.md                  # Keystone audit & architecture record
├── notebooks/
│   └── wikipedia_revenue_exploration.ipynb
├── src/
│   └── web_scraping/
│       ├── __init__.py
│       ├── cli.py                       # Unified CLI (`wikipedia` & `sec-edgar` subcommands)
│       ├── config.py                    # Validated immutable configuration (`ScraperConfig`)
│       ├── exceptions.py                # Explicit exception hierarchy
│       ├── http_client.py               # Session pooling, retry strategy & rate limiter
│       └── scrapers/
│           ├── __init__.py
│           ├── base.py                  # Abstract `BaseScraper` contract
│           ├── wikipedia.py             # `WikipediaCompaniesScraper`
│           └── sec_edgar.py             # `SecEdgarScraper`
└── tests/
    ├── test_config.py
    ├── test_wikipedia_scraper.py
    └── test_sec_edgar_scraper.py
```

## 3. Verification Invariants (`/verify`)

1. **Startup Config Validation:** `ScraperConfig` fails fast with `ConfigurationError` if `SCRAPER_USER_AGENT` is empty or numeric timeouts/retries are invalid.
2. **Deterministic Offline Testing:** All HTML parsers (`WikipediaCompaniesScraper.parse_html` and `SecEdgarScraper.parse_html`) are decoupled from network I/O so unit tests run deterministically offline in milliseconds.
3. **Zero Silent Data Loss:** Row column mismatches or unparseable pages log clear diagnostics or raise `ParsingError` with the offending URL attached.
