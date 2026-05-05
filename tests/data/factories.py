from datetime import datetime

from pyspark.sql import SparkSession

from example.myjobpackage.tables import (
    EXAMPLE_INPUT_SCHEMA,
    EXAMPLE_INPUT_TABLE,
    EXAMPLE_OUTPUT_SCHEMA,
)

EXPECTED_OUTPUT_TABLE = 'expected_output'


def example_input(spark: SparkSession):
    data = [
        (0, datetime(2024, 1, 8, 11, 0, 0), 'Jorge', 0.5876),
        (1, datetime(2024, 1, 11, 14, 28, 0), 'Ricardo', 0.42),
    ]
    return spark.createDataFrame(data, EXAMPLE_INPUT_SCHEMA)


def expected_output(spark: SparkSession):
    data = [
        (0, datetime(2024, 1, 8, 11, 0, 0), 'Jorge', 58.76),
        (1, datetime(2024, 1, 11, 14, 28, 0), 'Ricardo', 42.0),
    ]
    return spark.createDataFrame(data, EXAMPLE_OUTPUT_SCHEMA)


ALL_TABLES = {
    EXAMPLE_INPUT_TABLE: example_input,
    EXPECTED_OUTPUT_TABLE: expected_output,
}
