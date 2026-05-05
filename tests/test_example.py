import os

from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual
from pytest import fixture

from pysparkdt import reinit_local_metastore, spark_base
from example.myjobpackage.processing import process_data
from example.myjobpackage.tables import EXAMPLE_INPUT_TABLE, EXAMPLE_OUTPUT_TABLE
from tests.data.factories import (
    ALL_TABLES,
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
    process_data(
        spark=spark,
        input_table=EXAMPLE_INPUT_TABLE,
        output_table=EXAMPLE_OUTPUT_TABLE,
    )

    actual_output = spark.read.format('delta').table(EXAMPLE_OUTPUT_TABLE)
    expected_output = spark.read.format('delta').table(EXPECTED_OUTPUT_TABLE)

    assertDataFrameEqual(
        actual=actual_output.select(sorted(actual_output.columns)),
        expected=expected_output.select(sorted(expected_output.columns)),
    )
