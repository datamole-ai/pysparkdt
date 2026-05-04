import os

from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual
from pytest import fixture

from pysparkdt import reinit_local_metastore, spark_base
from tests.data.factories import (
    ALL_TABLES,
    EXAMPLE_INPUT_TABLE,
    EXPECTED_OUTPUT_TABLE,
)

DATA_DIR = f'{os.path.dirname(__file__)}/data'
TMP_DIR = f'{DATA_DIR}/tmp'
METASTORE_DIR = f'{TMP_DIR}/metastore'


@fixture(scope='module')
def spark():
    yield from spark_base(METASTORE_DIR)


def test_reinit_local_metastore_writes_all_factories(
    spark: SparkSession,
):
    reinit_local_metastore(spark, ALL_TABLES)

    actual_input = spark.read.format('delta').table(EXAMPLE_INPUT_TABLE)
    expected_output = spark.read.format('delta').table(EXPECTED_OUTPUT_TABLE)

    expected_input_df = ALL_TABLES[EXAMPLE_INPUT_TABLE](spark)
    expected_output_df = ALL_TABLES[EXPECTED_OUTPUT_TABLE](spark)

    assertDataFrameEqual(
        actual=actual_input.select(sorted(actual_input.columns)),
        expected=expected_input_df.select(sorted(expected_input_df.columns)),
    )
    assertDataFrameEqual(
        actual=expected_output.select(sorted(expected_output.columns)),
        expected=expected_output_df.select(sorted(expected_output_df.columns)),
    )
