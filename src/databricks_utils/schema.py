"""Schema validation helpers for PySpark DataFrames."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.types import StructType


class SchemaValidationError(ValueError):
    """Raised when a DataFrame's schema does not match the expected schema."""


def validate_schema(
    df: DataFrame,
    expected: StructType,
    *,
    check_nullable: bool = False,
    allow_extra_columns: bool = False,
) -> None:
    """Validate that ``df`` matches the ``expected`` schema.

    Raises ``SchemaValidationError`` listing every mismatch found: missing columns, unexpected
    extra columns (unless ``allow_extra_columns`` is True), column type mismatches, and — if
    ``check_nullable`` is True — nullability mismatches.
    """
    actual_fields = {f.name: f for f in df.schema.fields}
    expected_fields = {f.name: f for f in expected.fields}

    missing = expected_fields.keys() - actual_fields.keys()
    extra = actual_fields.keys() - expected_fields.keys()

    errors: list[str] = []
    if missing:
        errors.append(f"missing columns: {sorted(missing)}")
    if extra and not allow_extra_columns:
        errors.append(f"unexpected columns: {sorted(extra)}")

    for name in sorted(expected_fields.keys() & actual_fields.keys()):
        expected_field = expected_fields[name]
        actual_field = actual_fields[name]
        if actual_field.dataType != expected_field.dataType:
            errors.append(
                f"column '{name}' has type {actual_field.dataType}, "
                f"expected {expected_field.dataType}"
            )
        if check_nullable and actual_field.nullable != expected_field.nullable:
            errors.append(
                f"column '{name}' has nullable={actual_field.nullable}, "
                f"expected {expected_field.nullable}"
            )

    if errors:
        raise SchemaValidationError("; ".join(errors))
