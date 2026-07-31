# Overview

This document gives a more detailed overview to the repo project and also a good companion to the README. The
README tells you *how* to install and use this package. This page tells you
*what it is, why it exists, and how it works*. It is written in a way that makes it useful
whether you've never touched Databricks before or you're evaluating the
design choices yourself.

## What is this repo?

`shared-databricks-utils` is a small Python package with four utilities that
almost every Databricks/PySpark job ends up needing:

| Utility | What it does |
|---|---|
| `get_logger` | Console logging that behaves correctly inside Databricks notebooks |
| `load_config` | Loads YAML config files, with environment-variable substitution |
| `retry` | A decorator that retries a flaky function with exponential backoff |
| `validate_schema` | Checks a DataFrame's schema matches what you expect, before you use it |

None of these are novel ideas — they're the same handful of things every data
engineering team writes at some point. The point of this repo is to write
them **once, correctly, with tests**, instead of every downstream job
reinventing (and re-debugging) its own version.

## Why this repo exists

This is the first repo in a small series of Databricks-focused projects. It
was built first, deliberately, for two reasons:

1. **Other repos in the series will depend on it.** If the shared utilities
   are shaky, everything built on top of them inherits that instability. It
   made sense to get this one right before building anything that imports it.
2. **It's a good place to establish standards.** Because it's small, it's a
   low-stakes place to set the bar for the rest of the series: a proper
   package layout, real unit tests (including ones that exercise a local
   Spark session), CI that runs on every push, and documentation that
   explains *why*, not just *what*. Later repos in the series follow the same
   bar.

If you're reading this as a learning resource: the interesting part isn't
really "how do you write a retry decorator" (that's a few lines of code).
It's the surrounding practice — tests, CI, packaging, docs — that turns a
few useful functions into something a team can actually depend on. That
surrounding practice is what this repo is meant to demonstrate.

## How the repo is organized

```
shared-databricks-utils/
├── src/databricks_utils/     # the actual package (installable, importable)
│   ├── logging_utils.py
│   ├── config.py
│   ├── retry.py
│   └── schema.py
├── tests/                    # pytest tests, incl. a local Spark fixture
├── .github/workflows/ci.yml  # lint + test on every push/PR
├── pyproject.toml            # package metadata, dependencies, tool config
└── README.md                 # install + usage
```

It uses a `src/` layout (the package lives under `src/databricks_utils/`
rather than at the repo root). This is a standard Python packaging
convention that prevents accidentally importing the local source tree
instead of the installed package during testing.

## The utilities, explained

### `get_logger`: logging that survives notebook re-runs

**The problem:** In a Databricks notebook, re-running a cell that calls
`logging.getLogger(...)` and attaches a handler will attach *another* handler
each time, so every log line gets printed twice, then three times, then
four. It's a small annoyance that becomes very confusing during iterative
development.

**How it works:** `get_logger(name)` checks whether the logger already has a
handler attached before adding a new one, and disables propagation to the
root logger (which Databricks configures in ways that can also cause
duplicate output). Calling it 50 times with the same name is safe and always
returns a logger that prints each line exactly once.

### `load_config`: YAML config with environment awareness

**The problem:** A job usually needs slightly different settings in dev,
staging, and prod (a different table path, a different retry count) but you
don't want to hand-maintain three near-duplicate config files or hardcode
secrets into YAML.

**How it works:** `load_config` reads a YAML file and substitutes
`${VAR_NAME}` (or `${VAR_NAME:-default}` for an optional default) with values
from the environment, so a config file can reference `${ENVIRONMENT}` or
`${DB_HOST}` and pick up whatever's actually set at runtime, without secrets
ever being committed to the file. An optional `env_prefix` lets specific
environment variables (e.g. `MYJOB_RETRY_COUNT`) override individual config
keys entirely, for one-off overrides without editing the file.

### `retry`: surviving flaky reads/writes

**The problem:** Cloud storage and network calls fail transiently, like a
throttled API, a dropped connection, and the fix is almost always "try
again in a moment," not "crash the whole job."

**How it works:** `retry` is a decorator: wrap a function with
`@retry(max_attempts=3, base_delay=1.0, exceptions=(IOError,))` and it will
catch the listed exceptions, wait (doubling the delay each time, by default),
and try again, up to `max_attempts` times, before finally letting the last
exception through. Optional `jitter` adds a small random delay on top, which
matters more once you have many parallel tasks retrying at once; without
jitter, they'd all retry in lockstep and hammer the same endpoint again at
the same moment.

### `validate_schema`: catching schema drift early

**The problem:** An upstream table's schema can silently change, like a column
renamed, a type changed from `int` to `long`, and the first sign of trouble
is often a confusing failure deep inside a transformation, far from the
actual cause.

**How it works:** `validate_schema(df, expected_schema)` compares a
DataFrame's actual schema against an expected `StructType` and raises a
single error listing *every* mismatch it finds at once like missing columns,
unexpected extra columns, type mismatches, and (optionally) nullability
mismatches, so you find out immediately, with a clear message, right where
you read the data rather than three steps later.

## Testing and CI, briefly

The tests in `tests/` aren't just unit tests against pure Python; `schema.py`
is tested against a real local PySpark session (see `conftest.py`), because a
schema validator is only trustworthy if it's been checked against Spark's
actual behavior, not a guess at it. CI runs the same test suite on every push
and pull request across two Python versions, plus a separate lint job, so
regressions get caught before they reach `main`. See
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) for the exact setup.

## Further reading / planned tutorials

The list below is a set of some article topics that I plan on writing to give you more context into this project and also help with grasping the concept. They are planned for later, likely as
standalone articles on my Medium and Substack accounts.

They will go beyond this overview into full
walkthroughs and worked examples. Links will be added here as each one is
published.

- **Why loggers duplicate output in Databricks notebooks, and how to actually fix it**: a deeper look at `get_logger` and Python's logging handler/propagation model.
- **Environment-aware config for multi-environment Databricks jobs**: patterns for YAML + env-var interpolation, and where this approach breaks down (and what to reach for instead at larger scale).
- **Catching schema drift before it breaks your pipeline**: a practical guide to schema validation in PySpark, built around `validate_schema`.
- **Exponential backoff and jitter, explained**: why naive retries make outages worse, and how backoff + jitter fixes it.
- **From notebook to package**: structuring a reusable Databricks utility library with a `src/` layout and `pyproject.toml`.
- **Testing PySpark code locally**: session-scoped fixtures, a local Spark session in `conftest.py`, and what's worth testing versus mocking.
- **Setting up CI for a PySpark project**: lint + test matrices with GitHub Actions, and why the test job needs a JDK.
