import os
from datetime import datetime, timezone

from myjobpackage.processing import process_data
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from pyspark.testing import assertDataFrameEqual
from pytest import fixture

from pysparkdt import reinit_local_metastore, spark_base

DATA_DIR = f'{os.path.dirname(__file__)}/data'
TMP_DIR = f'{DATA_DIR}/tmp'
METASTORE_DIR = f'{TMP_DIR}/metastore_factories'

INPUT_TABLE = 'example_input'
OUTPUT_TABLE = 'output'
EXPECTED_OUTPUT_TABLE = 'expected_output'

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


def _input(spark: SparkSession) -> DataFrame:
    data = [
        (
            0,
            datetime(2024, 1, 8, 11, 0, 0, tzinfo=timezone.utc),
            'Jorge',
            0.5876,
        ),
        (
            1,
            datetime(2024, 1, 11, 14, 28, 0, tzinfo=timezone.utc),
            'Ricardo',
            0.42,
        ),
    ]
    return spark.createDataFrame(data, INPUT_SCHEMA)


def _expected_output(spark: SparkSession) -> DataFrame:
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


TABLE_FACTORIES = {
    INPUT_TABLE: _input,
    EXPECTED_OUTPUT_TABLE: _expected_output,
}


@fixture(scope='module')
def spark():
    yield from spark_base(METASTORE_DIR)


def test_process_data(
    spark: SparkSession,
):
    reinit_local_metastore(spark, table_factories=TABLE_FACTORIES)
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
