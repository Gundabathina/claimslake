# bronze/

Local Bronze layer output of the medallion architecture.

The ingestion engine (see the ingestion/ package) writes raw,
minimally-processed data here as Parquet, partitioned by ingestion date:

    bronze/<source>/ingestion_date=YYYY-MM-DD/<file>.parquet

## This directory is generated, not source-controlled

The Parquet files produced here are build artifacts: they are regenerated
by running the ingestion pipeline locally, so they are excluded from git
(see .gitignore) rather than committed. Only this README is tracked, so the
directory's purpose stays documented in the repo.

To populate it locally:

    pip install -r requirements.txt
    python -m ingestion.src.ingestion_engine --all

## Bronze-layer principle

Data written here preserves the source as faithfully as possible. The only
additions are technical metadata columns (ingestion_timestamp, source_file,
file_hash). No deduplication, no fixing invalid values, no business rules -
those transformations happen later in Silver (Milestone 3) and Gold
(Milestone 4).
