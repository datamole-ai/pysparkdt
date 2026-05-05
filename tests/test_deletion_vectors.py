import os

from pyspark.sql import SparkSession
from pytest import fixture

from example.myjobpackage.tables import EXAMPLE_INPUT_TABLE
from pysparkdt import reinit_local_metastore, spark_base
from tests.data.factories import ALL_TABLES

DATA_DIR = f'{os.path.dirname(__file__)}/data'
TMP_DIR = f'{DATA_DIR}/tmp'
METASTORE_DIR = f'{TMP_DIR}/metastore'


@fixture(scope='module')
def spark():
    yield from spark_base(METASTORE_DIR)


def test_deletion_vectors_disabled(spark: SparkSession):
    """Test that deletion vectors are disabled when deletion_vectors=False"""
    reinit_local_metastore(spark, ALL_TABLES, deletion_vectors=False)

    table_properties = spark.sql(
        f'DESCRIBE DETAIL {EXAMPLE_INPUT_TABLE}'
    ).collect()[0]
    properties = table_properties.properties

    assert properties.get('delta.enableDeletionVectors') == 'false'


def test_deletion_vectors_enabled(spark: SparkSession):
    """Test that deletion vectors are enabled when deletion_vectors=True"""
    reinit_local_metastore(spark, ALL_TABLES, deletion_vectors=True)

    table_properties = spark.sql(
        f'DESCRIBE DETAIL {EXAMPLE_INPUT_TABLE}'
    ).collect()[0]
    properties = table_properties.properties

    assert properties.get('delta.enableDeletionVectors') == 'true'
