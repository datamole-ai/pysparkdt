import os

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    LongType,
    StringType,
    StructField,
    StructType,
)
from pytest import fixture

from pysparkdt import reinit_local_metastore, spark_base

METASTORE_DIR = f'{os.path.dirname(__file__)}/data/tmp/metastore'

TEST_TABLE = 'deletion_vectors_test'
TEST_SCHEMA = StructType(
    [
        StructField('id', LongType(), nullable=False),
        StructField('name', StringType(), nullable=True),
    ]
)


def _build_test_table(spark: SparkSession):
    return spark.createDataFrame([(0, 'a'), (1, 'b')], TEST_SCHEMA)


TABLES = {TEST_TABLE: _build_test_table}


@fixture(scope='module')
def spark():
    yield from spark_base(METASTORE_DIR)


def test_deletion_vectors_disabled(spark: SparkSession):
    """Test that deletion vectors are disabled when deletion_vectors=False"""
    reinit_local_metastore(spark, TABLES, deletion_vectors=False)

    table_properties = spark.sql(f'DESCRIBE DETAIL {TEST_TABLE}').collect()[0]
    properties = table_properties.properties

    assert properties.get('delta.enableDeletionVectors') == 'false'


def test_deletion_vectors_enabled(spark: SparkSession):
    """Test that deletion vectors are enabled when deletion_vectors=True"""
    reinit_local_metastore(spark, TABLES, deletion_vectors=True)

    table_properties = spark.sql(f'DESCRIBE DETAIL {TEST_TABLE}').collect()[0]
    properties = table_properties.properties

    assert properties.get('delta.enableDeletionVectors') == 'true'
