# Web Scraping Toolkit (Wikipedia & SEC EDGAR)

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Architecture: Keystone](https://img.shields.io/badge/Architecture-Keystone-purple.svg)

A modular, resilient Python web scraping toolkit designed with **Keystone Engineering Framework** best practices. It extracts, cleans, validates, and exports structured financial and corporate datasets from **Wikipedia** (*List of largest companies in the United States by revenue*) and **SEC EDGAR Archives**.

Bu proje, **Wikipedia** üzerindeki ABD'nin gelir bakımından en büyük şirketleri tablosunu ve **SEC EDGAR** arşiv dizinlerini güvenli, hataya dayanıklı (retry, timeout, rate-limit destekli) ve modüler bir mimariyle çekip CSV formatında dışa aktaran profesyonel bir Python veri kazıma (web scraping) aracıdır.

## Key Features (Öne Çıkan Özellikler)

* **Resilient HTTP Layer (`HttpClient`):** Built on `requests.Session` with configurable `User-Agent` headers (required by both SEC EDGAR and Wikimedia policies), exponential backoff retries for transient errors (`429`, `500`, `502`, `503`, `504`), explicit request timeouts, and rate limiting.
* **Clean Data Extraction (`WikipediaCompaniesScraper`):**
  * Locates target tables deterministically by CSS class and header validation rather than fragile positional indexing.
  * Automatically strips Wikipedia footnote markers (e.g., `"4,000[2]"` $\rightarrow$ `"4,000"`), deduplicates records, and optionally normalizes numeric columns (`--clean-numbers`).
* **SEC EDGAR Directory Parser (`SecEdgarScraper`):**
  * Safely extracts Central Index Key (`CIK`), company names, and archive links across both legacy (`a.dir-entry2`) and standard SEC directory table layouts without silent `IndexError` failures.
* **Zero-Secret & Environment-Driven Config (`ScraperConfig`):** Validated at startup via `.env` and environment variables.
* **Comprehensive Test Suite:** Deterministic offline unit tests covering configuration validation, HTML parsing, edge cases, and error handling.

## Project Structure (Proje Dizin Yapısı)

```text
web-scraping/
├── .env.example                            # Ortam değişkenleri şablonu (Environment template)
├── .gitignore                              # Git takip dışı kuralları
├── CONTRIBUTING.md                         # Katkıda bulunma rehberi
├── LICENSE                                 # MIT Lisansı
├── README.md                               # Proje dokümantasyonu
├── main.py                                 # Hızlı CLI başlangıç betiği
├── pyproject.toml                          # Modern Python paket yapılandırması (PEP 621)
├── requirements.txt                        # Bağımlılık listesi
├── data/
│   └── sample_us_largest_companies.csv     # Temizlenmiş örnek veri seti (Top 100 ABD şirketi)
├── docs/
│   └── ARCHITECTURE.md                     # Keystone mimari kararları ve kod denetim raporu
├── notebooks/
│   └── wikipedia_revenue_exploration.ipynb # Örnek veri analizi Jupyter Notebook dosyası
├── src/
│   └── web_scraping/
│       ├── __init__.py
│       ├── cli.py                          # Komut satırı arayüzü (CLI)
│       ├── config.py                       # Ortam değişkeni doğrulama ve yapılandırma
│       ├── exceptions.py                   # Özel hata sınıfları (Custom exceptions)
│       ├── http_client.py                  # Retry, timeout ve User-Agent destekli HTTP istemcisi
│       └── scrapers/
│           ├── __init__.py
│           ├── base.py                     # Soyut temel kazıyıcı sınıfı (BaseScraper)
│           ├── wikipedia.py                # Wikipedia şirket tablosu kazıyıcısı
│           └── sec_edgar.py                # SEC EDGAR şirket/CIK dizin kazıyıcısı
└── tests/
    ├── test_config.py
    ├── test_sec_edgar_scraper.py
    └── test_wikipedia_scraper.py
```

## Quick Start (Hızlı Başlangıç)

### 1. Clone & Create Virtual Environment (Kurulum)

```bash
git clone https://github.com/<your-username>/web-scraping.git
cd web-scraping

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

### 2. Configure Environment Variables (`.env` Ayarları)

Copy `.env.example` to `.env` and set your descriptive `User-Agent` (mandatory for SEC EDGAR compliance):

```bash
cp .env.example .env
```

Example `.env` configuration:

```ini
SCRAPER_USER_AGENT="MyCompanyDataBot/1.0 (https://github.com/myuser/web-scraping; contact@mycompany.com)"
SCRAPER_TIMEOUT_SECONDS=15
SCRAPER_MAX_RETRIES=3
SCRAPER_RATE_LIMIT_DELAY=0.2
SCRAPER_OUTPUT_DIR="data"
```

### 3. Usage via CLI (Komut Satırı Kullanımı)

You can run the toolkit either via `python main.py` or the installed `web-scraper` console script:

```bash
# 1. Scrape Wikipedia Largest US Companies table to CSV
python main.py wikipedia --output us_largest_companies.csv

# Scrape Wikipedia table and normalize numeric columns (Revenue, Growth %, Employees)
python main.py wikipedia --clean-numbers --output us_largest_companies_numeric.csv

# 2. Scrape SEC EDGAR company directory to CSV
python main.py sec-edgar --output sec_edgar_companies.csv
```

### 4. Programmatic Usage in Python (Kod İçinden Kullanım)

```python
from web_scraping import ScraperConfig, WikipediaCompaniesScraper, SecEdgarScraper

config = ScraperConfig.from_env()

# Wikipedia Top US Companies
wiki_scraper = WikipediaCompaniesScraper(config=config, clean_numbers=True)
companies_df = wiki_scraper.scrape()
wiki_scraper.export_csv(companies_df, "us_largest_companies.csv")

# SEC EDGAR Directory
edgar_scraper = SecEdgarScraper(config=config)
edgar_df = edgar_scraper.scrape()
edgar_scraper.export_csv(edgar_df, "sec_edgar_companies.csv")
```

## Running Tests (Testleri Çalıştırma)

All unit tests run offline using deterministic HTML fixtures:

```bash
python -m unittest discover -s tests -v
```

## License (Lisans)

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
