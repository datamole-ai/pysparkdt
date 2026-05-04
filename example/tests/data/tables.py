"""Test-only table names and schemas for expected fixtures."""

from pyspark.sql.types import (
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

EXPECTED_OUTPUT_TABLE = 'expected_output'

EXPECTED_OUTPUT_SCHEMA = StructType(
    [
        StructField('id', LongType(), nullable=False),
        StructField('time_utc', TimestampType(), nullable=False),
        StructField('name', StringType(), nullable=True),
        StructField('result', DoubleType(), nullable=True),
    ]
)
