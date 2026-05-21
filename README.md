# pysparkdt (PySpark Delta Testing)

<p align="center">
    <a href="https://pypi.org/project/pysparkdt">
        <img src="https://img.shields.io/pypi/pyversions/pysparkdt.svg?color=%2334D058"
             alt="Supported Python versions">
    </a>
    <a href="https://pypi.org/project/pysparkdt" target="_blank">
        <img src="https://img.shields.io/pypi/v/pysparkdt?color=%2334D058&label=pypi%20package"
             alt="Package version">
    </a>
    <a href="https://pypi.org/project/pysparkdt">
        <img alt="PyPI - Downloads"
             src="https://img.shields.io/pypi/dm/pysparkdt.svg?label=PyPI%20downloads">
    </a>
    <a href="https://github.com/astral-sh/ruff">
        <img alt="Ruff"
             src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json">
    </a>
</p>

**An open-source Python library for simplifying local testing of Databricks 
workflows using PySpark and Delta tables.**

This library enables seamless testing of PySpark processing logic outside 
Databricks by **emulating Unity Catalog** behavior. It dynamically generates a 
local metastore to mimic Unity Catalog and supports simplified handling of 
Delta tables for both batch and streaming workloads.

# Guideline

## Table of Contents

- [Overview](#overview)
  - [Scope](#scope)
  - [Prerequisites](#prerequisites)
- [Setup](#setup)
  1. [Installation](#1-installation)
  2. [Testable Code](#2-testable-code)
  3. [File Structure](#3-file-structure)
  4. [Tests](#4-tests)
- [Advanced](#advanced)
  - [Testing Stream Processing](#testing-stream-processing)
  - [Mocking Inside RDD and UDF Operations](#mocking-inside-rdd-and-udf-operations)

## Overview

### Scope
This guideline helps you test Databricks Python pipelines with a 
focus on PySpark code. While basic unit testing knowledge with pytest is 
helpful, it's not the central focus.

### Key Points
- **Standalone Testing:** The setup allows you to test code without Databricks 
access, enabling easy CI integration.

- **Local Metastore:** Mimic the Databricks Unity Catalog using a dynamically 
generated local metastore with local Delta tables.

- **Code Testability:** Move core processing logic from notebooks to Python 
modules. Notebooks then serve as entrypoints.

## Setup
In the following section we will assume that you are creating tests for a 
job which has one delta table on input and produces one delta table on output. 
It utilizes PySpark for its processing.

### 1. Installation
**Install pysparkdt** 
- Get this package from the pypi. It's only needed in your test environment.

```bash
pip install pysparkdt
```

### 2. Testable code
- **Modularization:** Move processing logic from notebooks to modules.

- **Notebook Role:** Notebooks primarily handle initialization and triggering 
processing. They should contain all the code specific to Databricks 
(e.g. `dbutils` usage)

<div align="center">
<strong>entrypoint.py (Databricks Notebook)</strong>
</div>

```python
# Databricks notebook source
import sys
from pathlib import Path

MODULE_DIR = Path.cwd().parent
sys.path.append(MODULE_DIR.as_posix())

# COMMAND ----------

from myjobpackage.processing import process_data

# COMMAND ----------

input_table = dbutils.widgets.get('input_table')
output_table = dbutils.widgets.get('output_table')

# COMMAND ----------

process_data(
    spark=spark,
    input_table=input_table,
    output_table=output_table,
)
```
**myjobpackage.processing**
- Contains the core logic to test
- Our test focuses on the core function `myjobpackage.processing.process_data`

### 3. File structure

```
myjobpackage
├── __init__.py
├── entrypoint.py  # Databricks Notebook
├── processing.py
└── tables.py      # optional: names/schemas for tables the job uses
tests
├── __init__.py
├── test_processing.py
└── data
    └── factories.py  # ALL_TABLES, table names, schemas, factories
```

Put table fixtures under `tests/data/` (typically `factories.py` with a dict
such as `ALL_TABLES`). Import production schemas from your job package where
appropriate.

### 4. Tests

**Constants:** Define paths for test data and the temporary metastore.

```python
DATA_DIR = f'{os.path.dirname(__file__)}/data'
TMP_DIR = f'{DATA_DIR}/tmp'
METASTORE_DIR = f'{TMP_DIR}/metastore'
```

**Spark Fixture:** Define fixture for the local spark session using 
`spark_base` function from the testing package. Specify the temporal metastore 
location.

```python
from pytest import fixture
from pysparkdt import spark_base

@fixture(scope='module')
def spark():
    yield from spark_base(METASTORE_DIR)
```

**Table setup:** Use `reinit_local_metastore`

Call `reinit_local_metastore(spark, ALL_TABLES)` with a dict mapping each table name to
a callable `(spark) -> DataFrame` (see `tests.data.factories`). It drops **all
tables** in Spark's current schema (usually `default`). It does not drop
tables in other schemas. It then writes each factory output as Delta
(unqualified names in that schema). The
`deletion_vectors` argument defaults to on; pass `deletion_vectors=False`
to disable Delta deletion vectors.

*Alternatively, you can call this only once per testing module, but then
individual tests might affect each other by modifying tables.*

```python
from myjobpackage.processing import process_data
from myjobpackage.tables import INPUT_TABLE
from pysparkdt import reinit_local_metastore
from pyspark.testing import assertDataFrameEqual

from tests.data.factories import ALL_TABLES, EXPECTED_OUTPUT_TABLE


def test_process_data(
    spark: SparkSession,
):
    reinit_local_metastore(spark, ALL_TABLES)

    process_data(
        spark=spark,
        input_table=INPUT_TABLE,
        output_table='output',
    )

    output = spark.read.format('delta').table('output')
    expected = spark.read.format('delta').table(EXPECTED_OUTPUT_TABLE)

    assertDataFrameEqual(
        actual=output.select(sorted(output.columns)),
        expected=expected.select(sorted(expected.columns)),
    )
```

 In the example above, we use `assertDataFrameEqual` to compare PySpark 
 DataFrames. We ensure the columns are ordered so that the order of result 
 columns does not matter. By default, the order of rows does not matter in 
 `assertDataFrameEqual` (this can be adjusted using the `checkRowOrder` 
 parameter).

**ℹ️ For complete example, please look at [example](https://github.com/datamole-ai/pysparkdt/blob/main/example).**


**⚠️ Manual deletion of local metastore**

Deleting the local metastore manually invalidates any Spark session configured 
for that location. You would need to start a new Spark session because 
the original session’s state is no longer valid. Avoid manual deletion — 
use `reinit_local_metastore` for reinitialization instead.


**⚠️ Note on running tests in parallel**

With the setup above, the metastore is shared on the module scope. 
Therefore, if tests defined in the same module are run in parallel, 
race conditions can occur if multiple test functions use the same tables.

To mitigate this, make sure each test in the module uses its own set of tables.

## Advanced

### Testing Stream Processing

Let's now focus on a case where a job is reading input delta table using 
PySpark streaming, performing some computation on the data and saving it to 
the output delta table.

In order to be able to test the processing we need to explicitly wait for 
its completion. The best way to do it is to **await the streaming function 
performing the processing**.

To be able to await the streaming function, the **test function needs to have 
access to it**. Thus, we need to make sure the streaming function (query in 
Databricks terms) is accessible - for example by returning it by 
the processing function.

<div align="center">
<strong>myjobpackage/processing.py</strong>
</div>

```python
def process_data(
    spark: SparkSession,
    input_table: str, 
    output_table: str, 
    checkpoint_location: str,
) -> StreamingQuery:
  load_query = spark.readStream.format('delta').table(input_table)
    
  def process_batch(df: pyspark.sql.DataFrame, _) -> None:
      ... process df ...
      df.write.mode('append').format('delta').saveAsTable(output_table)

  return (
      load_query.writeStream.format('delta')
      .foreachBatch(process_batch)
      .trigger(availableNow=True)
      .option('checkpointLocation', checkpoint_location)
      .start()
  )
```

<div align="center">
<strong>myjobpackage/tests/test_processing.py</strong>
</div>

```python
def test_process_data(spark: SparkSession):
    ...
    spark_processing = process_data(
        spark=spark,
        input_table_name='input',
        output_table='output',
        checkpoint_location=f'{TMP_DIR}/_checkpoint/output',
    )
    spark_processing.awaitTermination(60)
    
    output = spark.read.format('delta').table('output')
    expected = spark.read.format('delta').table('expected_output')
    ...
```

### Mocking Inside RDD and UDF Operations

If we are testing whole job’s processing code and inside it we have functions 
executed through `rdd.mapPartitions`, `rdd.map`, or UDFs, we need to add 
special  handling for mocking as regular patching does not propagate to worker 
nodes.

<div align="center">
<strong>myjobpackage/processing.py</strong>
</div>

```python
myjobpackage/processing.py

def call_api(
    data_df: pyspark.sql.DataFrame,
) -> pyspark.sql.DataFrame:
    # Call API in parallel (session per partition)
    result = data_df.rdd.mapPartitions(_partition_run).toDF()
    return result
  
def _partition_run(
    iterable: Iterable[Row],
) -> Iterable[dict[str, Any]]:
  with ApiSessionClient() as client:
      for row in iterable:
          ...
          output = client.post(prepared_data)
          ...
          yield output
        
def process_data(
    data_df: pyspark.sql.DataFrame,
) -> pyspark.sql.DataFrame:
    ...
    ... = call_api(...)
    ...
```

 In this example we have a code that calls external API in `_partition_run`, 
 we do not want to call the actual API in our test, thus we want to mock 
 `ApiSessionClient`. 
 
```python
from pytest import fixture

def _mocked_session_post(json_data: dict):
    ...
    return output


@fixture
def api_session_client(mocker):
    api_session_client_mock = mocker.patch.object(
        myjobpackage.processing,
        'ApiSessionClient',
    )
    api_session_client_mock.return_value = session_client = mocker.Mock()
    session_client.__enter__ = mocker.Mock()
    session_client.__enter__.return_value = session_client_ctx = mocker.Mock()
    session_client.__exit__ = mocker.Mock()
    session_client_ctx.post = mocker.Mock(side_effect=_mocked_session_post)
    return session_client
```

As `ApiSessionClient` is created inside `rdd.mapPartitions` we need to also 
mock `call_api`.

```python
def _mocked_call_api(
    data_df: pyspark.sql.DataFrame,
) -> pyspark.sql.DataFrame:
    results = list(_partition_run(data_df.collect()))
    spark = SparkSession.builder.getOrCreate()
    pandas_df = pd.DataFrame(results)
    return spark.createDataFrame(pandas_df)


@fixture
def call_api_mock(mocker, api_session_client):
    mocker.patch.object(
        myjobpackage.processing, 'call_api', _mocked_call_api
    )
```

Then we can run the test with the mocked API.

```python
def test_process_data(
    spark: SparkSession,
    call_api_mock,
):
  ...
```

## License

pysparkdt is licensed under the [MIT
license](https://opensource.org/license/mit/). See the 
[LICENSE file](https://github.com/datamole-ai/pysparkdt/blob/main/LICENSE) for more details.

## How to Contribute

See [CONTRIBUTING.md](https://github.com/datamole-ai/pysparkdt/blob/main/CONTRIBUTING.md).
