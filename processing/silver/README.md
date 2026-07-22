# processing/silver/

Silver layer PySpark transformations: reads Bronze Parquet and produces cleaned, validated, standardized data.

Responsibilities (built in Milestone 3):

- Deduplication (e.g. duplicate claim submissions)
- Null handling and data type standardization
- Business rule validation (e.g. invalid diagnosis codes, negative paid amounts)
- Quarantining of records that fail validation, with reasons logged, instead of silently dropping them
- Late-arriving record handling
