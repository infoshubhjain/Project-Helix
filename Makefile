# Project Helix - Common tasks
# Usage: make [target]

.PHONY: install run test validate scrape-local scrape-modal lint help

# Default port (match run.sh)
PORT ?= 5001

help:
	@echo "Project Helix - available targets:"
	@echo "  make install      - Install Python deps and Playwright browser"
	@echo "  make run          - Start Flask app (port $(PORT))"
	@echo "  make test         - Run validation/smoke tests"
	@echo "  make validate     - Same as test"
	@echo "  make scrape-local - Run scrapers locally (no upload)"
	@echo "  make scrape-modal - Run scrapers via Modal (production)"
	@echo "  make lint         - Run flake8 on Project (optional)"

install:
	cd Project && pip install -r requirements.txt && playwright install chromium

run:
	./run.sh

test validate:
	python3 test_app.py

scrape-local:
	cd Project && python3 scrape.py

scrape-modal:
	cd Project && modal run scrape.py

lint:
	flake8 Project/*.py Project/calander/*.py Project/email_parser/*.py --max-line-length=120 2>/dev/null || echo "Install flake8: pip install flake8"
