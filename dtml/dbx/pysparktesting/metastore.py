import json
import os

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    BinaryType,
    BooleanType,
    ByteType,
    DateType,
    DecimalType,
    DoubleType,
    FloatType,
    IntegerType,
    LongType,
    ShortType,
    StringType,
    TimestampType,
)

# A mapping from type names in the JSON schema to PySpark types
TYPE_MAPPING = {
    'StringType': StringType,
    'BinaryType': BinaryType,
    'BooleanType': BooleanType,
    'DateType': DateType,
    'TimestampType': TimestampType,
    'DecimalType': DecimalType,
    'DoubleType': DoubleType,
    'FloatType': FloatType,
    'ByteType': ByteType,
    'IntegerType': IntegerType,
    'LongType': LongType,
    'ShortType': ShortType,
    # Add other types as needed
}


def reinit_local_metastore(
    spark: SparkSession,
    json_tables_dir: str,
) -> None:
    """Re-initializes dynamic metastore acting as Databricks data catalog
    using provided input delta table data in json format.

    For each delta table there should be <table_name>.ndjson file in the
    directory specified by json_tables_dir parameter. Optionally, there can
    also be the schema file under <json_tables_dir>/schema/<table_name>.json.

    The format of the schema file:
        [
          {
            "name": "id",
            "type": "LongType"
          },
          {
            "name": "name",
            "type": "StringType"
          },
          ...
        ]

    The mapping from type names in the schema json to PySpark types is
    defined by TYPE_MAPPING.

    As a part of the re-initialization it clears all existing tables before
    initializing the new ones.

    Parameters
    ----------
    spark
        Local Spark session.
    json_tables_dir
        Directory where the delta tables and their schemas are located.
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

        schema_mapping = {}
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as schema_file:
                schema_json = json.load(schema_file)

            schema_mapping = {
                field['name']: (TYPE_MAPPING[field['type']]())
                for field in schema_json
            }

        # Read JSON with inferred schema or partial custom schema
        df = (
            spark.read.format('json')
            .option('inferSchema', True)
            .load(data_path)
        )

        # Apply schema types to the DataFrame
        for column_name, column_type in schema_mapping.items():
            df = df.withColumn(column_name, df[column_name].cast(column_type))

        df.write.format('delta').saveAsTable(table_name)
