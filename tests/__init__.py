"""Test suite root package.

Makes `tests` a regular package so subpackages import as `tests.pyspark`
and `tests.ingestion` rather than as top-level `pyspark`/`ingestion`.
Without this file, pytest (pythonpath=["."], importlib mode) roots
`tests/pyspark/` as top-level `pyspark`, shadowing Apache PySpark and
breaking `from pyspark.sql import SparkSession`.
"""
