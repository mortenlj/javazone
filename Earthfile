ARG PY_VERSION=3.9
ARG EARTHLY_GIT_PROJECT_NAME
ARG BASEIMAGE=ghcr.io/$EARTHLY_GIT_PROJECT_NAME

FROM busybox

deps:
    FROM python:${PY_VERSION}-slim

    WORKDIR /app

    RUN apt-get --yes update && \
        apt-get --yes install build-essential libpq-dev

    RUN pip install poetry
    ENV POETRY_VIRTUALENVS_IN_PROJECT=true

    COPY pyproject.toml poetry.lock .
    RUN poetry install --no-dev --no-root --no-interaction

    SAVE ARTIFACT .venv
    SAVE IMAGE --cache-hint


build:
    FROM +deps

    RUN poetry install --no-root --no-interaction

    COPY --dir .prospector.yaml console tests alembic .
    RUN poetry install --no-interaction && \
        poetry run black --check . && \
        poetry run prospector && \
        poetry run pytest

    SAVE ARTIFACT alembic
    SAVE ARTIFACT console
    SAVE IMAGE --cache-hint

test:
    LOCALLY
    RUN poetry install --no-interaction && \
        poetry run black --check . && \
        poetry run prospector && \
        poetry run pytest

black:
    LOCALLY
    RUN poetry install --no-interaction && \
        poetry run black .

docker:
    FROM navikt/python:${PY_VERSION}
    ARG EARTHLY_GIT_SHORT_HASH
    ARG IMAGE_TAG=$EARTHLY_GIT_SHORT_HASH

    WORKDIR /app

    COPY --dir +deps/.venv .
    COPY --dir +build/alembic .
    COPY --dir +build/console .

    ENV PATH="/bin:/usr/bin:/usr/local/bin:/app/.venv/bin"

    CMD ["/app/.venv/bin/python", "-m", "console"]

    SAVE IMAGE --push ${BASEIMAGE}:${IMAGE_TAG} ${BASEIMAGE}:latest
