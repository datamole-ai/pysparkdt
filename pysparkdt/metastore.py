import json
import os

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType


def reinit_local_metastore(
    spark: SparkSession,
    json_tables_dir: str,
    deletion_vectors: bool = True,
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

    Parameters
    ----------
    spark
        Local Spark session.
    json_tables_dir
        Directory where the delta tables and their schemas are located.
    deletion_vectors
        Whether to enable deletion vectors for the delta tables.
        Defaults to True.
    """
    # Clear all existing tables (must be done through SQL, not by clearing the
    # folder)
    existing_tables = spark.sql('SHOW TABLES').select('tableName').collect()
    for table in existing_tables:
        spark.sql(f'DROP TABLE {table.tableName}')

    tables = [
        name
        for name in os.listdir(json_tables_dir)
        if name.endswith('.ndjson')
    ]
    for table_file in tables:
        table_name, _ = os.path.splitext(table_file)
        data_path = f'{json_tables_dir}/{table_file}'
        schema_path = f'{json_tables_dir}/schema/{table_name}.json'

        if os.path.exists(schema_path):
            # Read the JSON schema from the file as dictionary
            with open(schema_path, 'r') as schema_file:
                schema_dict = json.load(schema_file)

            # Load the schema from the dictionary
            schema = StructType.fromJson(schema_dict)
        else:
            schema = None

        # Read table with appropriate schema - custom if the schema file is
        # present, inferred otherwise
        query = spark.read.format('json')
        if schema is not None:
            query = query.schema(schema)
        else:
            query = query.option('inferSchema', True)
        df = query.load(data_path)

        write_query = df.write.format('delta')

        if deletion_vectors:
            write_query = write_query.option(
                'delta.enableDeletionVectors', 'true'
            )
        else:
            write_query = write_query.option(
                'delta.enableDeletionVectors', 'false'
            )
        write_query.saveAsTable(table_name)
