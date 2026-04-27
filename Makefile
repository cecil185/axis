.PHONY: install test test-unit run serve clean shell build

install: build

test:
	poetry run pytest tests/ -v

test-unit:
	poetry run pytest tests/ -v -k "not browser"

serve:
	poetry run python -m src.server

run:
	poetry run python -m src.game

shell:
	poetry run bash

clean:
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
