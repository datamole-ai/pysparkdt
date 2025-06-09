import os

from pyspark.sql import SparkSession
from pytest import fixture

from pysparkdt import reinit_local_metastore, spark_base

DATA_DIR = f'{os.path.dirname(__file__)}/data'
JSON_TABLES_DIR = f'{DATA_DIR}/tables'
TMP_DIR = f'{DATA_DIR}/tmp'
METASTORE_DIR = f'{TMP_DIR}/metastore'


@fixture(scope='module')
def spark():
    yield from spark_base(METASTORE_DIR)


def test_deletion_vectors_enabled(spark: SparkSession):
    """Test that deletion vectors are enabled when deletion_vectors=True"""
    reinit_local_metastore(spark, JSON_TABLES_DIR, deletion_vectors=True)

    # Check if deletion vectors are enabled for the table
    table_properties = spark.sql('DESCRIBE DETAIL example_input').collect()[0]
    properties = table_properties.properties

    assert properties.get('delta.enableDeletionVectors') == 'true'


def test_deletion_vectors_default_behavior(spark: SparkSession):
    """Test that deletion vectors are disabled by default"""
    reinit_local_metastore(spark, JSON_TABLES_DIR)

    # Check if deletion vectors are disabled for the table (default behavior)
    table_properties = spark.sql('DESCRIBE DETAIL example_input').collect()[0]
    properties = table_properties.properties

    # When deletion vectors are not explicitly enabled,
    # the property should not be set to 'true'
    assert properties.get('delta.enableDeletionVectors') != 'true'
