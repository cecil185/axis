.PHONY: install test run clean shell build

build:
	docker compose build

install: build

test:
	docker compose run --rm app pytest tests/ -v

run:
	docker compose run --rm app python -m src.game

shell:
	docker compose run --rm app bash

clean:
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
