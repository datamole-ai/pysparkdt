from collections.abc import Callable

from pyspark.sql import DataFrame, SparkSession

TableFactory = Callable[[SparkSession], DataFrame]


def _write_table(
    spark: SparkSession,
    name: str,
    factory: TableFactory,
    *,
    deletion_vectors: bool = True,
) -> None:
    df = factory(spark)
    (
        df.write
        .format('delta')
        .option('delta.enableDeletionVectors', str(deletion_vectors).lower())
        .saveAsTable(name)
    )


def _drop_all_tables(spark: SparkSession) -> None:
    """Drop every table in Spark's current database."""
    existing_tables = spark.sql('SHOW TABLES').select('tableName').collect()
    for table in existing_tables:
        spark.sql(f'DROP TABLE `{table.tableName}`')


def reinit_local_metastore(
    spark: SparkSession,
    tables: dict[str, TableFactory],
    deletion_vectors: bool = True,
) -> None:
    """Re-initialize the local metastore from table factories.

    Drops every table in Spark's current database, then writes each entry
    as Delta in that database.

    Parameters
    ----------
    spark
        Local Spark session.
    tables
        Mapping from table name to a ``TableFactory`` (function that takes a
        ``SparkSession`` and returns a ``DataFrame``).
    deletion_vectors
        Whether to enable deletion vectors for the delta tables.
        Defaults to True.
    """
    _drop_all_tables(spark)
    for name, factory in tables.items():
        _write_table(spark, name, factory, deletion_vectors=deletion_vectors)
