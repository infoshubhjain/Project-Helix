# Project Helix - Common tasks
# Usage: make [target]

.PHONY: install test test-py test-js validate scrape-local help

help:
	@echo "Project Helix - available targets:"
	@echo "  make install      - Install Python deps and Playwright browser"
	@echo "  make test         - Run Python + JavaScript test suites"
	@echo "  make test-py      - Run Python tests only"
	@echo "  make test-js      - Run JavaScript tests only"
	@echo "  make scrape-local - Run scrapers locally to update JSON"
	@echo "  make help         - Show this help message"

install:
	cd Project && pip install -r requirements.txt && playwright install --with-deps chromium

test: test-py test-js

test-py:
	python3 -m unittest discover -s tests -v

test-js:
	node --test tests/js/*.test.js

validate:
	cd Project && python3 -m py_compile scrape.py && echo "Python syntax validation passed"

scrape-local:
	cd Project && python3 scrape.py
