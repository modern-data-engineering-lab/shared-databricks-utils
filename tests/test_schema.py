from __future__ import annotations

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from databricks_utils.schema import SchemaValidationError, validate_schema

EXPECTED_SCHEMA = StructType(
    [
        StructField("id", IntegerType(), nullable=False),
        StructField("name", StringType(), nullable=True),
    ]
)


def test_validate_schema_passes_for_matching_schema(spark: SparkSession) -> None:
    df = spark.createDataFrame([(1, "a")], schema=EXPECTED_SCHEMA)

    validate_schema(df, EXPECTED_SCHEMA)  # should not raise


def test_validate_schema_raises_for_missing_column(spark: SparkSession) -> None:
    df = spark.createDataFrame([(1,)], schema=StructType([StructField("id", IntegerType())]))

    with pytest.raises(SchemaValidationError, match="missing columns"):
        validate_schema(df, EXPECTED_SCHEMA)


def test_validate_schema_raises_for_unexpected_extra_column(spark: SparkSession) -> None:
    actual_schema = StructType(
        [
            StructField("id", IntegerType()),
            StructField("name", StringType()),
            StructField("extra", StringType()),
        ]
    )
    df = spark.createDataFrame([(1, "a", "x")], schema=actual_schema)

    with pytest.raises(SchemaValidationError, match="unexpected columns"):
        validate_schema(df, EXPECTED_SCHEMA)


def test_validate_schema_allows_extra_column_when_permitted(spark: SparkSession) -> None:
    actual_schema = StructType(
        [
            StructField("id", IntegerType()),
            StructField("name", StringType()),
            StructField("extra", StringType()),
        ]
    )
    df = spark.createDataFrame([(1, "a", "x")], schema=actual_schema)

    validate_schema(df, EXPECTED_SCHEMA, allow_extra_columns=True)  # should not raise


def test_validate_schema_raises_for_type_mismatch(spark: SparkSession) -> None:
    actual_schema = StructType(
        [
            StructField("id", StringType()),
            StructField("name", StringType()),
        ]
    )
    df = spark.createDataFrame([("1", "a")], schema=actual_schema)

    with pytest.raises(SchemaValidationError, match="column 'id' has type"):
        validate_schema(df, EXPECTED_SCHEMA)


def test_validate_schema_checks_nullable_when_enabled(spark: SparkSession) -> None:
    actual_schema = StructType(
        [
            StructField("id", IntegerType(), nullable=True),
            StructField("name", StringType(), nullable=True),
        ]
    )
    df = spark.createDataFrame([(1, "a")], schema=actual_schema)

    with pytest.raises(SchemaValidationError, match="nullable"):
        validate_schema(df, EXPECTED_SCHEMA, check_nullable=True)


def test_validate_schema_ignores_nullable_by_default(spark: SparkSession) -> None:
    actual_schema = StructType(
        [
            StructField("id", IntegerType(), nullable=True),
            StructField("name", StringType(), nullable=True),
        ]
    )
    df = spark.createDataFrame([(1, "a")], schema=actual_schema)

    validate_schema(df, EXPECTED_SCHEMA)  # should not raise
