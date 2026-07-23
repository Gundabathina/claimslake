"""
conftest.py

Shared pytest fixtures for the PySpark Silver tests.

A single local SparkSession is created once per test session (Spark
startup is slow, so re-creating it per test would make the suite
painfully slow). Tests use small in-memory DataFrames and exercise the
real transformation functions - no assert-True placeholders.

These tests require pyspark (and a JVM/Java 8/11/17) to be installed;
see spark_jobs/README.md for environment requirements. They are written to
be run locally - this project's authoring environment cannot execute
Spark, so the suite is provided code-complete and statically reviewed,
with local execution still required.
"""

import pytest

from spark_jobs.src.spark_session import get_spark_session


@pytest.fixture(scope="session")
def spark():
    session = get_spark_session("claimslake-silver-tests")
    yield session
    session.stop()
