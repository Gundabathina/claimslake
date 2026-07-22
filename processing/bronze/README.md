# processing/bronze/

Bronze layer processing: takes files landed by the ingestion layer and writes them as raw Parquet, partitioned by ingestion date, with minimal transformation (light type casting and the addition of ingestion metadata columns only). No business logic, deduplication, or cleaning happens here — Bronze preserves the raw source truth so any downstream bug can be traced back and reprocessed.
