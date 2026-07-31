"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark() -> Iterator[SparkSession]:
    """Session-scoped local SparkSession for tests that need a DataFrame."""
    session = (
        SparkSession.builder.master("local[2]")
        .appName("databricks-utils-tests")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    yield session
    session.stop()
