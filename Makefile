.PHONY: install test run clean shell build

install: build

test:
	poetry run pytest tests/ -v

run:
	poetry run python -m src.game

shell:
	poetry run bash

clean:
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
