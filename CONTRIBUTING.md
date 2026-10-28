# Contributing Guide (Katkıda Bulunma Rehberi)

Thank you for your interest in contributing to **Web Scraping Toolkit**! This document provides guidelines and engineering standards (built on the **Keystone Engineering Framework**) for contributing to this repository.

Projeye katkıda bulunmak istediğiniz için teşekkürler! Bu rehber, açık kaynak standartlarına ve **Keystone** mühendislik ilkelerine uygun geliştirme yapmanız için hazırlanmıştır.

## 1. Engineering Constraints & Guardrails (Mühendislik İlkeleri)

- **No Committed Virtual Environments or Secrets:** Never commit `venv/`, `.venv/`, `.env`, or local system paths (`pyvenv.cfg`). Always verify with `git status` before staging.
- **No Silent Failures:** Never use bare `except:` or `except IndexError: continue` without structured logging or explicit error handling.
- **HTTP Politeness & Compliance:**
  - Always send a descriptive `User-Agent` header configured via `.env` (`SCRAPER_USER_AGENT`).
  - Always specify an explicit `timeout` on every HTTP call.
  - Respect rate limits (especially SEC EDGAR's 10 requests/second policy).
- **Clean Notebooks:** Strip massive raw HTML outputs before committing `.ipynb` files so diffs remain human-readable.
- **Type Safety & Vectorized Data Processing:** Avoid $O(N^2)$ row-by-row `DataFrame.loc` appends inside loops; collect parsed records as typed dictionaries/dataclasses first, then construct the `pd.DataFrame` once.

## 2. Development Setup (Geliştirme Ortamı Kurulumu)

1. **Fork & Clone the Repository:**
   ```bash
   git clone https://github.com/<your-username>/web-scraping.git
   cd web-scraping
   ```

2. **Create an Isolated Virtual Environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies (Editable Mode):**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```

## 3. Running Tests & Verification (Test ve Doğrulama)

Before opening a Pull Request, ensure all tests pass and the CLI runs cleanly:

```bash
# Run the test suite
python -m unittest discover -s tests -v

# Verify CLI help and configuration
python main.py --help
```

## 4. Pull Request Checklist

- [ ] Code adheres to modular `src/web_scraping/` structure.
- [ ] Unit tests added or updated in `tests/` for any new parser or scraper logic.
- [ ] All tests pass (`python -m unittest discover -s tests -v`).
- [ ] Documentation (`README.md` or docstrings) updated to reflect user-facing changes.
- [ ] No `.env`, `venv/`, or large raw HTML dumps included in the commit.
