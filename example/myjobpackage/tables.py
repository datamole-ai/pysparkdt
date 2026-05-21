"""Schemas and table names for Delta tables this job uses."""

from pyspark.sql.types import (
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

INPUT_TABLE = 'input'
OUTPUT_TABLE = 'output'

INPUT_SCHEMA = StructType(
    [
        StructField('id', LongType(), nullable=False),
        StructField('time_utc', TimestampType(), nullable=False),
        StructField('name', StringType(), nullable=True),
        StructField('feature', DoubleType(), nullable=True),
    ]
)

OUTPUT_SCHEMA = StructType(
    [
        StructField('id', LongType(), nullable=False),
        StructField('time_utc', TimestampType(), nullable=False),
        StructField('name', StringType(), nullable=True),
        StructField('result', DoubleType(), nullable=True),
    ]
)
