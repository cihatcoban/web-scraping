#!/usr/bin/env python3
"""Root entry point allowing execution without prior package installation."""

from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from web_scraping.cli import main

if __name__ == "__main__":
    sys.exit(main())
