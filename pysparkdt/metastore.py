from collections.abc import Callable

from pyspark.sql import DataFrame, SparkSession

TableFactory = Callable[[SparkSession], DataFrame]


def _write_table(
    spark: SparkSession,
    name: str,
    factory: TableFactory,
    *,
    tbl_properties: dict[str, str] | None = None,
) -> None:
    """Write factory output as Delta; optional TBLPROPERTIES after write."""
    df = factory(spark)
    df.write.format('delta').mode('overwrite').saveAsTable(name)
    if tbl_properties:
        props = ', '.join(f"'{k}'='{v}'" for k, v in tbl_properties.items())
        spark.sql(f'ALTER TABLE {name} SET TBLPROPERTIES ({props})')


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
    as Delta in that database (unqualified table names, same as the historic
    NDJSON-based ``reinit_local_metastore``). Other databases are not scanned
    for drops.

    Every table gets ``delta.enableDeletionVectors`` from ``deletion_vectors``
    via ``ALTER TABLE ... SET TBLPROPERTIES`` after the write.

    Iteration follows dict insertion order.

    Parameters
    ----------
    spark
        Local Spark session.
    tables
        Mapping from table name to a ``TableFactory`` (``(spark) -> DataFrame``).
    deletion_vectors
        Whether to set ``delta.enableDeletionVectors`` on every table
        (``'true'`` / ``'false'``). Defaults to ``True``.
    """
    _drop_all_tables(spark)
    dv = {
        'delta.enableDeletionVectors': (
            'true' if deletion_vectors else 'false'
        )
    }
    for name, factory in tables.items():
        _write_table(spark, name, factory, tbl_properties=dv)
