import os
import shutil
from collections.abc import Iterator, Mapping

from delta import configure_spark_with_delta_pip
from pyspark import SparkContext
from pyspark.sql import SparkSession


def spark_base(
    metastore_dir: str | os.PathLike[str],
    *,
    master: str | None = None,
    spark_config: Mapping[str, str | int | float | bool] | None = None,
) -> Iterator[SparkSession]:
    """Creates and yields a Spark session configured for local run with
    dynamically created local metastore acting as the Databricks data catalog.

    It ensures proper teardown by stopping the session and resetting the
    SparkContext gateway and JVM by being generator.

    Only 1 session can be active at the time (previous session will be
    stopped).

    Intended to be used as a pytest fixture, e.g.

    @fixture(scope='module')
    def spark():
        yield from spark_base(METASTORE_DIR)

    Parameters
    ----------
    metastore_dir : str or path-like
        The directory to use for the dynamically created metastore.
    master : str, optional
        Spark master URL, for example ``local[2]``. If omitted, Spark uses its
        configured default. This value takes precedence over ``spark.master``
        in ``spark_config``.
    spark_config : mapping, optional
        Additional Spark builder configuration. Values provided for the
        following keys are ignored because pysparkdt replaces them with its
        required values: ``spark.app.name``, ``spark.sql.warehouse.dir``,
        ``spark.driver.extraJavaOptions``,
        ``spark.sql.catalogImplementation``, ``spark.sql.extensions``,
        ``spark.sql.catalog.spark_catalog``,
        ``spark.sql.session.timeZone``, and ``spark.jars.packages``. If
        ``master`` is provided, a ``spark.master`` value in ``spark_config``
        is also ignored.

    Yields
    ------
    SparkSession
        SparkSession object. After the test execution, the SparkSession is
        stopped and related resources are reset.

    Examples
    --------
    In a test file:

    @fixture(scope='module')
    def spark():
        yield from spark_base(
            METASTORE_DIR,
            master='local[2]',
            spark_config={
                'spark.default.parallelism': 2,
                'spark.sql.shuffle.partitions': 2,
            },
        )
    """
    metastore_dir = os.fsdecode(metastore_dir)
    existing = SparkSession.getActiveSession()
    if existing:
        # Spark state can persist across test modules even when using
        # module-scoped fixtures. Manually tear down any existing session
        # to avoid metastore reuse issues.
        _teardown_spark_session(existing, metastore_dir)

    # Create a Spark session with caller settings and required Delta defaults.
    builder = SparkSession.builder
    for key, value in (spark_config or {}).items():
        builder = builder.config(key, value)
    if master is not None:
        builder = builder.master(master)

    builder = (
        builder.appName('test_app')
        .config('spark.sql.warehouse.dir', metastore_dir)
        .config(
            'spark.driver.extraJavaOptions',
            f'-Dderby.system.home={metastore_dir}',
        )
        .enableHiveSupport()
        .config(
            'spark.sql.extensions',
            'io.delta.sql.DeltaSparkSessionExtension',
        )
        .config(
            'spark.sql.catalog.spark_catalog',
            'org.apache.spark.sql.delta.catalog.DeltaCatalog',
        )
        .config('spark.sql.session.timeZone', 'UTC')
    )

    # Create spark context
    session = configure_spark_with_delta_pip(builder).getOrCreate()
    session.sparkContext.setLogLevel('ERROR')
    yield session

    # Teardown: this runs after the module's tests complete. However,
    # Spark sessions can leak between modules, so we also do a cleanup
    # before session creation to ensure isolation.
    _teardown_spark_session(session, metastore_dir)


def _teardown_spark_session(session: SparkSession, metastore_dir: str) -> None:
    """Stop the Spark session and reset the gateway and JVM."""
    session.stop()
    SparkContext._gateway = None
    SparkContext._jvm = None
    shutil.rmtree(metastore_dir)
