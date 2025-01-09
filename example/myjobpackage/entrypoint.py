# Databricks notebook source
import sys
from pathlib import Path

MODULE_DIR = Path.cwd().parent
sys.path.append(MODULE_DIR.as_posix())

# COMMAND ----------

from myjobpackage.processing import process_data

# COMMAND ----------

input_table = dbutils.widgets.get('input_table')  # noqa: F821
output_table = dbutils.widgets.get('output_table')  # noqa: F821

# COMMAND ----------

process_data(
    session=spark,  # noqa: F821
    input_table=input_table,
    output_table=output_table,
)
