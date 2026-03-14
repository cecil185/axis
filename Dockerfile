# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Pygame runtime deps (SDL, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app
COPY pyproject.toml poetry.lock* README.md ./
COPY src/ src/
COPY tests/ tests/
RUN poetry install

ENV PYTHONPATH=/app
# Headless Pygame (no display)
ENV SDL_VIDEODRIVER=dummy

CMD ["pytest", "tests/", "-v"]
