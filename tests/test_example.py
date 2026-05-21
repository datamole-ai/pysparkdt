import os
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual
from pytest import fixture

from example.myjobpackage.processing import process_data
from example.myjobpackage.tables import (
    INPUT_SCHEMA,
    INPUT_TABLE,
    OUTPUT_SCHEMA,
    OUTPUT_TABLE,
)
from pysparkdt import reinit_local_metastore, spark_base

METASTORE_DIR = f'{os.path.dirname(__file__)}/data/tmp/metastore'

EXPECTED_OUTPUT_TABLE = 'expected_output'


def _input(spark: SparkSession):
    data = [
        (0, datetime(2024, 1, 8, 11, 0, 0), 'Jorge', 0.5876),
        (1, datetime(2024, 1, 11, 14, 28, 0), 'Ricardo', 0.42),
    ]
    return spark.createDataFrame(data, INPUT_SCHEMA)


def _expected_output(spark: SparkSession):
    data = [
        (0, datetime(2024, 1, 8, 11, 0, 0), 'Jorge', 58.76),
        (1, datetime(2024, 1, 11, 14, 28, 0), 'Ricardo', 42.0),
    ]
    return spark.createDataFrame(data, OUTPUT_SCHEMA)


ALL_TABLES = {
    INPUT_TABLE: _input,
    EXPECTED_OUTPUT_TABLE: _expected_output,
}


@fixture(scope='module')
def spark():
    yield from spark_base(METASTORE_DIR)


def test_process_data(
    spark: SparkSession,
):
    reinit_local_metastore(spark, ALL_TABLES)
    process_data(
        spark=spark,
        input_table=INPUT_TABLE,
        output_table=OUTPUT_TABLE,
    )
    output = spark.read.format('delta').table(OUTPUT_TABLE)
    expected = spark.read.format('delta').table(EXPECTED_OUTPUT_TABLE)
    assertDataFrameEqual(
        actual=output.select(sorted(output.columns)),
        expected=expected.select(sorted(expected.columns)),
    )
