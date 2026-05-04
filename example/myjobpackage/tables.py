"""Schemas and table names for Delta tables this job uses in production."""

from pyspark.sql.types import (
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

EXAMPLE_INPUT_TABLE = 'example_input'

EXAMPLE_INPUT_SCHEMA = StructType(
    [
        StructField('id', LongType(), nullable=False),
        StructField('time_utc', TimestampType(), nullable=False),
        StructField('name', StringType(), nullable=True),
        StructField('feature', DoubleType(), nullable=True),
    ]
)
