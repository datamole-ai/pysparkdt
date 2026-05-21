import os
from datetime import datetime, timezone

from myjobpackage.tables import (
    INPUT_TABLE,
    OUTPUT_SCHEMA,
)
from pyspark.sql import SparkSession

from pysparkdt import ndjson_table_factory

EXPECTED_OUTPUT_TABLE = 'expected_output'

_TABLES_DIR = f'{os.path.dirname(__file__)}/tables'


def expected_output(spark: SparkSession):
    data = [
        (
            0,
            datetime(2024, 1, 8, 11, 0, 0, tzinfo=timezone.utc),
            'Jorge',
            58.76,
        ),
        (
            1,
            datetime(2024, 1, 11, 14, 28, 0, tzinfo=timezone.utc),
            'Ricardo',
            42.0,
        ),
    ]
    return spark.createDataFrame(data, OUTPUT_SCHEMA)


ALL_TABLES = {
    INPUT_TABLE: ndjson_table_factory(f'{_TABLES_DIR}/example_input.ndjson'),
    EXPECTED_OUTPUT_TABLE: expected_output,
}
