import os

from myjobpackage.processing import process_data
from myjobpackage.tables import INPUT_TABLE, OUTPUT_TABLE
from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual
from pytest import fixture

from pysparkdt import reinit_local_metastore, spark_base
from tests.data.factories import ALL_TABLES, EXPECTED_OUTPUT_TABLE

DATA_DIR = f'{os.path.dirname(__file__)}/data'
TMP_DIR = f'{DATA_DIR}/tmp'
METASTORE_DIR = f'{TMP_DIR}/metastore'


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
