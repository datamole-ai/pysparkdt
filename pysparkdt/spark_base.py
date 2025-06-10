import shutil
from typing import Iterator

from delta import configure_spark_with_delta_pip
from pyspark import SparkContext
from pyspark.sql import SparkSession


def spark_base(metastore_dir: str) -> Iterator[SparkSession]:
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
    metastore_dir : str
        The directory to use for the dynamically created metastore.

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
        yield from spark_base(METASTORE_DIR)
    """
    existing = SparkSession.getActiveSession()
    if existing:
        # Spark state can persist across test modules even when using
        # module-scoped fixtures. Manually tear down any existing session
        # to avoid metastore reuse issues.
        _teardown_spark_session(existing, metastore_dir)

    #  Create a spark session with Delta
    builder = (
        SparkSession.builder.appName('test_app')
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


def _teardown_spark_session(
    session: SparkSession, metastore_dir: str = None
) -> None:
    """Stop the Spark session and reset the gateway and JVM"""
    session.stop()
    SparkContext._gateway = None
    SparkContext._jvm = None
    shutil.rmtree(metastore_dir)
