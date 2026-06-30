from pyspark.sql import SparkSession
from pyspark.sql.types import (
    LongType,
    StringType,
    StructField,
    StructType,
)
from pyspark.testing import assertDataFrameEqual
from pytest import fixture, raises

from pysparkdt import reinit_local_metastore, spark_base

TEST_TABLE = 'factory_test'
TEST_SCHEMA = StructType(
    [
        StructField('id', LongType(), nullable=False),
        StructField('name', StringType(), nullable=True),
    ]
)


def _build_table(spark: SparkSession):
    return spark.createDataFrame([(0, 'a'), (1, 'b')], TEST_SCHEMA)


@fixture(scope='module')
def spark(tmp_path_factory):
    yield from spark_base(tmp_path_factory.mktemp('metastore'))


def test_reinit_requires_exactly_one_source():
    with raises(ValueError, match='Exactly one'):
        reinit_local_metastore(None)  # type: ignore[arg-type]
    with raises(ValueError, match='Exactly one'):
        reinit_local_metastore(
            None,  # type: ignore[arg-type]
            '/dir',
            table_factories={TEST_TABLE: _build_table},
        )


def test_table_factories(spark: SparkSession):
    reinit_local_metastore(spark, table_factories={TEST_TABLE: _build_table})

    actual = spark.read.format('delta').table(TEST_TABLE)
    expected = _build_table(spark)
    assertDataFrameEqual(actual, expected)

