import os

from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual
from pytest import fixture

from pysparkdt import reinit_local_metastore, spark_base

from .processing import process_data

DATA_DIR = f'{os.path.dirname(__file__)}/data'
JSON_TABLES_DIR = f'{DATA_DIR}/tables'
TMP_DIR = f'{DATA_DIR}/tmp'
METASTORE_DIR = f'{TMP_DIR}/metastore'


@fixture(scope='module')
def spark():
    yield from spark_base(METASTORE_DIR)


def test_process_data(
    spark: SparkSession,
):
    reinit_local_metastore(spark, JSON_TABLES_DIR)
    process_data(
        session=spark,
        input_table='example_input',
        output_table='output',
    )
    output = spark.read.format('delta').table('output')
    expected = spark.read.format('delta').table('expected_output')
    assertDataFrameEqual(
        actual=output.select(sorted(output.columns)),
        expected=expected.select(sorted(expected.columns)),
    )
