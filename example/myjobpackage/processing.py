from pyspark.sql import SparkSession
from pyspark.sql.functions import col


def process_data(
    input_table: str, output_table: str, spark: SparkSession
) -> None:
    df = spark.read.table(input_table)
    df = df.withColumn('result', col('feature') * 100)
    df = df.drop('feature')
    df.write.format('delta').mode('overwrite').saveAsTable(output_table)
