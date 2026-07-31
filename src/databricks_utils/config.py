"""Config loading: YAML files with environment-variable interpolation and overrides."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

_ENV_VAR_PATTERN = re.compile(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(:-(?P<default>[^}]*))?\}")


class ConfigError(ValueError):
    """Raised when a config file is malformed or a required env var is missing."""


def _interpolate_env_vars(value: Any) -> Any:
    if isinstance(value, str):

        def _replace(match: re.Match[str]) -> str:
            var_name = match.group("name")
            default = match.group("default")
            if var_name in os.environ:
                return os.environ[var_name]
            if default is not None:
                return default
            raise ConfigError(
                f"environment variable '{var_name}' is not set and no default was given"
            )

        return _ENV_VAR_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _interpolate_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate_env_vars(v) for v in value]
    return value


def load_config(path: str | Path, *, env_prefix: str | None = None) -> dict[str, Any]:
    """Load a YAML config file.

    String values may reference environment variables with ``${VAR_NAME}`` or
    ``${VAR_NAME:-default}`` syntax. If ``env_prefix`` is given, any environment variable named
    ``{env_prefix}_{KEY}`` overrides the top-level ``key`` (lowercased) in the loaded config.
    """
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    if not isinstance(raw, dict):
        raise ConfigError(
            f"top-level config in {config_path} must be a mapping, got {type(raw).__name__}"
        )

    config: dict[str, Any] = _interpolate_env_vars(raw)

    if env_prefix:
        prefix = f"{env_prefix}_"
        for env_key, env_value in os.environ.items():
            if env_key.startswith(prefix):
                config[env_key[len(prefix):].lower()] = env_value

    return config
