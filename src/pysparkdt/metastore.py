import json
import os
from collections.abc import Callable

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType

TableFactory = Callable[[SparkSession], DataFrame]


def reinit_local_metastore(
    spark: SparkSession,
    json_tables_dir: str | os.PathLike[str] | None = None,
    deletion_vectors: bool = True,
    table_factories: dict[str, TableFactory] | None = None,
) -> None:
    """Re-initializes dynamic metastore acting as Databricks data catalog
    using provided input delta table data in json format.

    For each delta table there should be <table_name>.ndjson file in the
    directory specified by json_tables_dir parameter. Optionally, there can
    also be the schema file under <json_tables_dir>/schema/<table_name>.json.
    The format of the schema file is defined by PySpark StructType json
    representation.

    A schema file for a loaded DataFrame "df" can be created using:
        with(open(new_schema_file_path, 'w')) as file:
            file.write(json.dumps(df.schema.jsonValue(), indent=4))

    Example of a schema file:
        {
            "type": "struct",
            "fields": [
                {
                    "name": "id",
                    "type": "string",
                    "nullable": true,
                    "metadata": {}
                },
                ...
                {
                    "name": "time",
                    "type": "timestamp",
                    "nullable": true,
                    "metadata": {}
                }
            ]
        }

    As a part of the re-initialization all existing tables are dropped before
    the new ones are initialized.

    Alternatively, pass ``table_factories`` instead of ``json_tables_dir`` to
    define tables programmatically.

    Parameters
    ----------
    spark
        Local Spark session.
    json_tables_dir
        Directory where the delta tables and their schemas are located.
        Mutually exclusive with ``table_factories``.
    deletion_vectors
        Whether to enable deletion vectors for the delta tables.
        Defaults to True.
    table_factories
        Mapping from table name to a callable that takes a ``SparkSession``
        and returns a ``DataFrame``. Alternative to ``json_tables_dir``.
        Mutually exclusive with ``json_tables_dir``.

    Notes
    -----
    Exactly one of ``json_tables_dir`` and ``table_factories`` must be
    provided.
    """
    if (json_tables_dir is None) == (table_factories is None):
        raise ValueError(
            'Exactly one of json_tables_dir or table_factories must be '
            'provided'
        )
    if json_tables_dir is not None:
        tables = _ndjson_dir_to_tables(os.fsdecode(json_tables_dir))
    else:
        assert table_factories is not None
        tables = table_factories
    _drop_all_tables(spark)
    for name, factory in tables.items():
        _write_table(spark, name, factory, deletion_vectors=deletion_vectors)


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
    existing_tables = (
        spark.sql('SHOW TABLES').select('tableName', 'isTemporary').collect()
    )
    for table in existing_tables:
        if table.isTemporary:
            continue
        spark.sql(f'DROP TABLE `{table.tableName}`')


def _ndjson_table_factory(
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


def _ndjson_dir_to_tables(
    json_tables_dir: str,
) -> dict[str, TableFactory]:
    """Build a ``{table_name: TableFactory}`` dict from every ``*.ndjson``
    file in ``json_tables_dir``.

    For each delta table there should be a ``<table_name>.ndjson`` file
    in ``json_tables_dir``. Optionally, there can also be a schema file
    under ``<json_tables_dir>/schema/<table_name>.json``. The format of
    the schema file is defined by PySpark ``StructType`` JSON
    representation.

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
        os.path.splitext(table_file)[0]: _ndjson_table_factory(
            f'{json_tables_dir}/{table_file}'
        )
        for table_file in tables
    }
