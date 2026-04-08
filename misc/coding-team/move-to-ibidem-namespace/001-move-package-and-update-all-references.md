# Task: Move `javazone` package under `ibidem` namespace

## Context

The project has a top-level Python package `javazone/`. It needs to become `ibidem/javazone/` (i.e., `ibidem.javazone` in import space). The project name in `pyproject.toml` stays `javazone`.

## Objective

Restructure the Python package from `javazone` to `ibidem.javazone` and update every reference accordingly.

## Scope

### 1. Move the directory

- `git mv javazone ibidem/javazone` (create `ibidem/` first, with an empty `__init__.py`)
- Result: `ibidem/__init__.py` (empty) and `ibidem/javazone/` containing everything that was in `javazone/`

### 2. Update `pyproject.toml` (root)

- Keep `name = "javazone"` unchanged.
- There is no `[tool.setuptools]` or `[build-system]` section currently. The package discovery by `uv` should auto-detect `ibidem/` as the top-level package. Verify this works; if not, add minimal config to make it work.

### 3. Rewrite all Python imports in `ibidem/javazone/**/*.py`

Every file under `ibidem/javazone/` that imports from `javazone.*` must change to `ibidem.javazone.*`. Use absolute imports everywhere. Specifically:

- `from javazone.X import Y` → `from ibidem.javazone.X import Y`
- `import javazone.X` → `import ibidem.javazone.X`
- Relative imports like `from .X import Y`, `from ..X import Y`, `from ...X import Y` → convert to absolute `from ibidem.javazone.<full.path> import Y`

The one exception: `ibidem/javazone/__main__.py` currently has `from .main import main`. Convert this to `from ibidem.javazone.main import main`.

### 4. Update Dagger build pipeline (`dagger/src/main/__init__.py`)

Three references to update:
- Line 73: `.with_directory("/app/javazone", self.source.directory("javazone"))` → `.with_directory("/app/ibidem", self.source.directory("ibidem"))`
- Line 93: `.with_directory("/app/javazone", src.directory("/app/javazone"))` → `.with_directory("/app/ibidem", src.directory("/app/ibidem"))`
- Line 96: `.with_entrypoint(["/app/.venv/bin/python", "-m", "javazone"])` → `.with_entrypoint(["/app/.venv/bin/python", "-m", "ibidem.javazone"])`

### 5. Update tests if needed

`tests/test_dummy.py` has no imports from `javazone`, so no change needed. Verify.

## Non-goals

- Do NOT rename Kubernetes resources, service names, hostnames, Docker image names, or the Dagger class name `Javazone`.
- Do NOT change `dagger.json` module name.
- Do NOT change `docker-compose.yml` service names or env vars (e.g., `POSTGRES_USER: javazone` stays).
- Do NOT change deploy YAML files — all `javazone` references there are infrastructure names, not Python imports.
- Do NOT change `.github/workflows/main.yaml` — no Python import references there.
- Do NOT change `dagger/pyproject.toml` — it's for the Dagger SDK, unrelated.

## Constraints

- Use `git mv` for the directory move so git tracks the rename.
- All imports must be absolute (no relative imports in the final state).
- Project must pass: `uv sync`, `uv run black --check .`, `ruff check`, `uv run pytest`.
