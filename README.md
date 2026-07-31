# shared-databricks-utils

[![CI](https://github.com/modern-data-engineering-lab/shared-databricks-utils/actions/workflows/ci.yml/badge.svg)](https://github.com/modern-data-engineering-lab/shared-databricks-utils/actions/workflows/ci.yml)

Common utilities for Databricks/PySpark jobs: logging, config loading, schema
validation, and retry/backoff — shared across our Databricks repos so each one
isn't reinventing the same boilerplate.

📖 **New here?** See [`docs/OVERVIEW.md`](docs/OVERVIEW.md) for a full
walkthrough of what this repo is, why it exists, and how each utility works —
written for any level of experience, plus a list of planned deep-dive
tutorials.

## Why this exists

Every Databricks job ends up needing the same handful of things: a logger that
doesn't spam duplicate output when a notebook cell re-runs, a way to load YAML
config with environment-specific overrides, a check that an upstream table's
schema hasn't drifted, and a retry wrapper for flaky reads/writes. Instead of
copy-pasting that into every repo, it lives here once, tested and versioned.

## Install

```bash
pip install git+https://github.com/modern-data-engineering-lab/shared-databricks-utils.git
```

Pin to a specific commit or tag for reproducible builds:

```bash
pip install git+https://github.com/modern-data-engineering-lab/shared-databricks-utils.git@<tag-or-sha>
```

For local development:

```bash
pip install -e ".[dev]"
```

## Usage

```python
from databricks_utils import get_logger, load_config, retry, validate_schema

logger = get_logger(__name__)

config = load_config("config.yaml", env_prefix="MYJOB")

@retry(max_attempts=3, base_delay=1.0, exceptions=(IOError,))
def read_upstream_table():
    ...

validate_schema(df, expected_schema)
```

See the docstrings in `src/databricks_utils/` for each utility's full
options (env-var interpolation syntax for `load_config`, backoff/jitter
tuning for `retry`, nullability checks for `validate_schema`, etc.).

## Development

Requires a JDK (Spark needs one for local test runs, e.g. via
`actions/setup-java` in CI, or `pip install install-jdk` locally).

```bash
pip install -e ".[dev]"
ruff check .
pytest
```
