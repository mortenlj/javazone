VERSION 0.7

IMPORT github.com/mortenlj/earthly-lib/kubernetes/commands AS lib-k8s-commands

FROM busybox

deps:
    FROM python:3.10-slim

    WORKDIR /app

    RUN pip install poetry
    ENV POETRY_VIRTUALENVS_IN_PROJECT=true

    COPY pyproject.toml poetry.lock .
    RUN poetry install --no-dev --no-root --no-interaction

    SAVE ARTIFACT .venv
    SAVE IMAGE --cache-hint


build:
    FROM +deps

    RUN poetry install --no-root --no-interaction

    COPY --dir .prospector.yaml javazone tests .
    RUN poetry install --no-interaction && \
        poetry run black --check . && \
        poetry run prospector && \
        poetry run pytest

    SAVE ARTIFACT javazone
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
    FROM python:3.10-slim

    WORKDIR /app

    COPY --dir +deps/.venv .
    COPY --dir +build/javazone .

    ENV PATH="/bin:/usr/bin:/usr/local/bin:/app/.venv/bin"

    CMD ["/app/.venv/bin/python", "-m", "javazone"]

    # builtins must be declared
    ARG EARTHLY_GIT_PROJECT_NAME
    ARG EARTHLY_GIT_SHORT_HASH

    # Override from command-line on CI
    ARG main_image=ghcr.io/$EARTHLY_GIT_PROJECT_NAME
    ARG VERSION=$EARTHLY_GIT_SHORT_HASH

    SAVE IMAGE --push ${main_image}:${VERSION} ${main_image}:latest

manifests:
    ARG main_image=ghcr.io/$EARTHLY_GIT_PROJECT_NAME
    ARG VERSION=$EARTHLY_GIT_SHORT_HASH
    DO lib-k8s-commands+ASSEMBLE_MANIFESTS --IMAGE=${main_image} --VERSION=${VERSION}

deploy:
    BUILD --platform=linux/amd64 --platform=linux/arm64 +docker
    BUILD +manifests
