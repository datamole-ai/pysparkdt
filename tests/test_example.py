import os
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual
from pytest import fixture

from example.myjobpackage.processing import process_data
from example.myjobpackage.tables import (
    INPUT_TABLE,
    OUTPUT_SCHEMA,
    OUTPUT_TABLE,
)
from pysparkdt import (
    ndjson_table_factory,
    reinit_local_metastore,
    spark_base,
)

METASTORE_DIR = f'{os.path.dirname(__file__)}/data/tmp/metastore'
EXAMPLE_TABLES_DIR = (
    f'{os.path.dirname(__file__)}/../example/tests/data/tables'
)

EXPECTED_OUTPUT_TABLE = 'expected_output'


def _expected_output(spark: SparkSession):
    data = [
        (0, datetime(2024, 1, 8, 11, 0, 0, tzinfo=timezone.utc), 'Jorge', 58.76),
        (1, datetime(2024, 1, 11, 14, 28, 0, tzinfo=timezone.utc), 'Ricardo', 42.0),
    ]
    return spark.createDataFrame(data, OUTPUT_SCHEMA)


ALL_TABLES = {
    INPUT_TABLE: ndjson_table_factory(
        f'{EXAMPLE_TABLES_DIR}/example_input.ndjson',
    ),
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
