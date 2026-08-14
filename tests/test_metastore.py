import os
from collections.abc import Iterator
from pathlib import Path

from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql.types import (
    LongType,
    StringType,
    StructField,
    StructType,
)
from pyspark.testing import assertDataFrameEqual
from pytest import TempPathFactory, fixture, raises

from pysparkdt import reinit_local_metastore, spark_base

TEST_TABLE = 'factory_test'
TEST_SCHEMA = StructType(
    [
        StructField('id', LongType(), nullable=False),
        StructField('name', StringType(), nullable=True),
    ]
)


def _build_table(spark: SparkSession) -> DataFrame:
    return spark.createDataFrame([(0, 'a'), (1, 'b')], TEST_SCHEMA)


def _directory_entry(path: Path) -> os.DirEntry[str]:
    with os.scandir(path.parent) as entries:
        return next(entry for entry in entries if entry.name == path.name)


@fixture(scope='module')
def spark(tmp_path_factory: TempPathFactory) -> Iterator[SparkSession]:
    metastore_dir = tmp_path_factory.mktemp('metastore')
    yield from spark_base(
        _directory_entry(metastore_dir),
        master='local[2]',
        spark_config={
            'spark.master': 'local[1]',
            'spark.default.parallelism': 2,
            'spark.sql.shuffle.partitions': 2,
            'spark.sql.session.timeZone': 'Europe/Prague',
        },
    )


def test_spark_base_applies_resource_configuration(
    spark: SparkSession,
) -> None:
    assert spark.sparkContext.master == 'local[2]'
    assert spark.sparkContext.defaultParallelism == 2
    assert spark.conf.get('spark.sql.shuffle.partitions') == '2'
    assert spark.conf.get('spark.sql.session.timeZone') == 'UTC'


def test_pathlike_json_tables_dir(
    spark: SparkSession,
    tmp_path: Path,
) -> None:
    tables_dir = tmp_path / 'tables'
    tables_dir.mkdir()
    (tables_dir / f'{TEST_TABLE}.ndjson').write_text(
        '{"id": 0, "name": "a"}\n{"id": 1, "name": "b"}\n'
    )

    reinit_local_metastore(spark, _directory_entry(tables_dir))

    assert spark.table(TEST_TABLE).orderBy('id').collect() == [
        Row(id=0, name='a'),
        Row(id=1, name='b'),
    ]


def test_reinit_requires_exactly_one_source() -> None:
    with raises(ValueError, match='Exactly one'):
        reinit_local_metastore(None)  # type: ignore[arg-type]
    with raises(ValueError, match='Exactly one'):
        reinit_local_metastore(
            None,  # type: ignore[arg-type]
            '/dir',
            table_factories={TEST_TABLE: _build_table},
        )


def test_table_factories(spark: SparkSession) -> None:
    reinit_local_metastore(spark, table_factories={TEST_TABLE: _build_table})

    actual = spark.read.format('delta').table(TEST_TABLE)
    expected = _build_table(spark)
    assertDataFrameEqual(actual, expected)
