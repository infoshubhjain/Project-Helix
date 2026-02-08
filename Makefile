# Project Helix - Common tasks
# Usage: make [target]

.PHONY: install test validate scrape-local help

help:
	@echo "Project Helix - available targets:"
	@echo "  make install      - Install Python deps and Playwright browser"
	@echo "  make scrape-local - Run scrapers locally to update JSON"
	@echo "  make help         - Show this help message"

install:
	cd Project && pip install -r requirements.txt && playwright install chromium

test validate:
	python3 test_scrapers.py

scrape-local:
	cd Project && python3 scrape.py
