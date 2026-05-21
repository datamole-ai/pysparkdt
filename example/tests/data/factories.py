from datetime import datetime

from myjobpackage.tables import (
    INPUT_SCHEMA,
    INPUT_TABLE,
    OUTPUT_SCHEMA,
)
from pyspark.sql import SparkSession

EXPECTED_OUTPUT_TABLE = 'expected_output'


def input_data(spark: SparkSession):
    data = [
        (0, datetime(2024, 1, 8, 11, 0, 0), 'Jorge', 0.5876),
        (1, datetime(2024, 1, 11, 14, 28, 0), 'Ricardo', 0.42),
    ]
    return spark.createDataFrame(data, INPUT_SCHEMA)


def expected_output(spark: SparkSession):
    data = [
        (0, datetime(2024, 1, 8, 11, 0, 0), 'Jorge', 58.76),
        (1, datetime(2024, 1, 11, 14, 28, 0), 'Ricardo', 42.0),
    ]
    return spark.createDataFrame(data, OUTPUT_SCHEMA)


ALL_TABLES = {
    INPUT_TABLE: input_data,
    EXPECTED_OUTPUT_TABLE: expected_output,
}
