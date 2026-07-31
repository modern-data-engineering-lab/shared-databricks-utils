from __future__ import annotations

from pathlib import Path

import pytest

from databricks_utils.config import ConfigError, load_config


def test_load_config_basic_yaml(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("name: my-job\nretries: 3\n")

    config = load_config(config_file)

    assert config == {"name": "my-job", "retries": 3}


def test_load_config_interpolates_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CATALOG_NAME", "prod_catalog")
    config_file = tmp_path / "config.yaml"
    config_file.write_text("catalog: ${CATALOG_NAME}\n")

    config = load_config(config_file)

    assert config == {"catalog": "prod_catalog"}


def test_load_config_uses_default_when_env_var_missing(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("env: ${DEPLOY_ENV:-dev}\n")

    config = load_config(config_file)

    assert config == {"env": "dev"}


def test_load_config_raises_when_env_var_missing_and_no_default(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("token: ${MISSING_TOKEN}\n")

    with pytest.raises(ConfigError, match="MISSING_TOKEN"):
        load_config(config_file)


def test_load_config_interpolates_nested_structures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOST", "db.internal")
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "database:\n  host: ${HOST}\n  ports:\n    - 5432\n    - ${HOST}\n"
    )

    config = load_config(config_file)

    assert config == {"database": {"host": "db.internal", "ports": [5432, "db.internal"]}}


def test_load_config_applies_env_prefix_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MYAPP_RETRIES", "10")
    config_file = tmp_path / "config.yaml"
    config_file.write_text("retries: 3\nname: my-job\n")

    config = load_config(config_file, env_prefix="MYAPP")

    assert config["retries"] == "10"
    assert config["name"] == "my-job"


def test_load_config_raises_for_non_mapping_top_level(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("- one\n- two\n")

    with pytest.raises(ConfigError, match="must be a mapping"):
        load_config(config_file)
