import json
import os
from collections.abc import Callable

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType

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
        df.write.format('delta')
        .option('delta.enableDeletionVectors', str(deletion_vectors).lower())
        .saveAsTable(name)
    )


def _drop_all_tables(spark: SparkSession) -> None:
    existing_tables = spark.sql('SHOW TABLES').select('tableName').collect()
    for table in existing_tables:
        spark.sql(f'DROP TABLE `{table.tableName}`')


def reinit_local_metastore(
    spark: SparkSession,
    tables: dict[str, TableFactory],
    deletion_vectors: bool = True,
) -> None:
    """Re-initialize the local metastore from table factories.

    As a part of the re-initialization all existing tables are dropped
    before the new ones are initialized.

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


def ndjson_table_factory(
    ndjson_path: str,
    schema: StructType | None = None,
) -> TableFactory:
    """Return a ``TableFactory`` that loads rows from an NDJSON file.

    If ``schema`` is not provided, the sibling
    ``<dirname(ndjson_path)>/schema/<basename>.json`` is used when present
    (the format is defined by PySpark ``StructType`` JSON representation).
    Otherwise the schema is inferred by Spark.

    Parameters
    ----------
    ndjson_path
        Path to the NDJSON file containing the table rows.
    schema
        Explicit schema to apply when reading the NDJSON file.
    """
    if schema is None:
        table_name, _ = os.path.splitext(os.path.basename(ndjson_path))
        schema_path = (
            f'{os.path.dirname(ndjson_path)}/schema/{table_name}.json'
        )
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as schema_file:
                schema_dict = json.load(schema_file)
            schema = StructType.fromJson(schema_dict)

    def factory(spark: SparkSession) -> DataFrame:
        query = spark.read.format('json')
        if schema is not None:
            query = query.schema(schema)
        else:
            query = query.option('inferSchema', True)
        return query.load(ndjson_path)

    return factory


def ndjson_dir_to_tables(
    json_tables_dir: str,
) -> dict[str, TableFactory]:
    """Build a ``{table_name: TableFactory}`` dict from every ``*.ndjson``
    file in ``json_tables_dir``.

    For each delta table there should be a ``<table_name>.ndjson`` file
    in ``json_tables_dir``. Optionally, there can also be a schema file
    under ``<json_tables_dir>/schema/<table_name>.json``. The format of
    the schema file is defined by PySpark ``StructType`` JSON
    representation.

    Pipe the result straight into ``reinit_local_metastore`` (or merge
    with a dict of code-defined factories).

    Parameters
    ----------
    json_tables_dir
        Directory containing ``*.ndjson`` files (one per table) and an
        optional ``schema/`` subdirectory with companion ``StructType``
        JSON files.
    """
    tables = [
        name
        for name in os.listdir(json_tables_dir)
        if name.endswith('.ndjson')
    ]
    return {
        os.path.splitext(table_file)[0]: ndjson_table_factory(
            f'{json_tables_dir}/{table_file}'
        )
        for table_file in tables
    }
