VERSION 0.8

IMPORT github.com/mortenlj/earthly-lib/kubernetes/commands AS lib-k8s-commands

FROM busybox

deps:
    FROM python:3.12-slim

    WORKDIR /app

    RUN pip install poetry
    ENV POETRY_VIRTUALENVS_IN_PROJECT=true

    COPY pyproject.toml poetry.lock .
    RUN poetry install --only main --no-root --no-interaction

    SAVE ARTIFACT .venv
    SAVE IMAGE --cache-hint


build:
    FROM +deps

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

reseal-secret:
    FROM ghcr.io/mortenlj/kafka-debug:20240502140355-1d44edf

    COPY .env .
    RUN --mount=type=secret,id=kubeconfig,target=/root/.kube/config \
        kubectl create secret generic --dry-run=client --namespace default -ojson javazone --from-env-file=.env | \
        jq '.metadata.labels.app="javazone"' | \
        kubeseal -ojson | \
        jq '.metadata.labels.app="javazone"' | \
        yq -Poyaml > sealed-secret.yaml
    SAVE ARTIFACT sealed-secret.yaml AS LOCAL deploy/sealed-secret.yaml

docker:
    FROM python:3.12-slim

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
    # builtins must be declared
    ARG EARTHLY_GIT_PROJECT_NAME
    ARG EARTHLY_GIT_SHORT_HASH

    ARG main_image=ghcr.io/$EARTHLY_GIT_PROJECT_NAME
    ARG VERSION=$EARTHLY_GIT_SHORT_HASH
    DO lib-k8s-commands+ASSEMBLE_MANIFESTS --IMAGE=${main_image} --VERSION=${VERSION}

deploy:
    BUILD --platform=linux/amd64 --platform=linux/arm64 +docker
    BUILD +manifests
