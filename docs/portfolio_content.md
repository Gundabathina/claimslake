# ClaimsLake — Portfolio Content

Ready-to-use content for GitHub, LinkedIn, resumes, and interviews. Every claim below is based only on implemented and verified features. All data in the project is synthetic; the Terraform AWS architecture is reference-only and has never been applied.

## Repository description (≤350 characters)

> End-to-end healthcare-claims data engineering platform on a medallion (Bronze/Silver/Gold) architecture: Python ingestion, PySpark cleaning + quarantine, dbt-duckdb star schema, 35 analytical SQL queries, Airflow orchestration, multi-job GitHub Actions CI, and a Terraform AWS (S3/Glue/Athena) reference architecture. Synthetic data only.

(Approximately 340 characters — trim if a platform enforces a hard 350 limit.)

## Recommended GitHub topics

`data-engineering` · `medallion-architecture` · `pyspark` · `dbt` · `duckdb` · `airflow` · `terraform` · `aws` · `etl` · `data-pipeline` · `sql-analytics` · `data-quality` · `healthcare-data` · `github-actions` · `portfolio-project`

## Pinned repository summary

ClaimsLake — a production-style healthcare-claims data platform built end to end: config-driven ingestion, PySpark Silver transformations with a quarantine path, a dbt-duckdb Gold star schema (incl. SCD2 provider history), a 35-query analytical SQL layer, Airflow orchestration, CI across five test suites, and a Terraform AWS reference architecture. 100% synthetic data.

## LinkedIn Projects description

ClaimsLake is an end-to-end data engineering project that turns messy, synthetic healthcare claims files into analytics-ready tables using a medallion (Bronze → Silver → Gold) architecture. I built config-driven Python ingestion with retries and metadata tracking, PySpark transformations that clean, deduplicate, and validate records (routing bad rows to a quarantine path instead of dropping them), and a dbt-duckdb Gold star schema with SCD2 provider history. On top of Gold sits a curated 35-query analytical SQL layer. The pipeline is orchestrated with Apache Airflow and validated by a multi-job GitHub Actions CI (ingestion, PySpark, SQL, scripts, Airflow, plus dbt parse). I also authored a Terraform AWS reference architecture (S3 data-lake layers, Glue Data Catalog + crawlers, Athena workgroup, least-privilege IAM) that is CI-validated with fmt/init/validate but intentionally never deployed, so it incurs no cost. All data is synthetic.

## Resume bullets (ATS-friendly)

- Built an end-to-end healthcare-claims data pipeline on a medallion (Bronze/Silver/Gold) architecture using Python, PySpark, dbt, and DuckDB, including a quarantine path that isolates invalid records with reasons instead of dropping them.
- Modeled a Gold star schema with dbt (fact + dimensions, SCD Type 2 provider history) and authored a 35-query analytical SQL layer covering members, providers, claims, finance, and data quality.
- Automated quality gates with a multi-job GitHub Actions CI across five pytest suites plus dbt parse, and authored a Terraform AWS (S3/Glue/Athena, least-privilege IAM) reference architecture validated in CI (fmt/init/validate).

## 30-second project explanation

ClaimsLake is a portfolio data-engineering project that ingests synthetic healthcare claims and turns them into analytics-ready tables. Raw files land in a Bronze layer, PySpark cleans and validates them into Silver — quarantining bad records — and dbt builds a Gold star schema on DuckDB. A 35-query SQL layer sits on top, Airflow orchestrates the stages, and GitHub Actions runs the full test suite on every push. I also wrote a Terraform AWS reference architecture that is CI-validated but never deployed.

## Two-minute technical walkthrough

ClaimsLake follows the medallion pattern with synthetic healthcare claims data across four datasets: members, providers, diagnoses, and claims.

Ingestion is config-driven Python. Sources are declared in YAML, and the engine supports full and incremental loads with retry handling, structured logging, and per-batch metadata tracking. It writes a raw Bronze layer in Parquet, keeping every column as a string so nothing is lost before validation.

The Silver layer is PySpark. It casts types with explicit schemas, standardizes fields (for example trimming and upper-casing state codes), and performs deterministic two-stage deduplication. Validation applies business rules — invalid records (like future dates of birth or bad state codes) are routed to a quarantine path with a rejection reason and timestamp, while non-fatal issues are flagged with data-quality columns and kept. Provider records preserve each versioned row, which is the raw material for SCD Type 2.

The Gold layer is dbt using the dbt-duckdb adapter. DuckDB reads the Silver Parquet directly, so there is no separate load step. The models build a star schema: fact_claims plus dim_member and dim_provider (with SCD2 history), all covered by dbt tests.

On top of Gold, a curated SQL layer provides 35 analytical queries grouped by domain, with a master runner and a catalog doc.

Everything is orchestrated by an Airflow DAG that wires ingest → Silver → dbt build → dbt test. Quality is enforced by a multi-job GitHub Actions CI (ingestion, PySpark, SQL, scripts, and Airflow suites, plus a dbt parse check) and a separate, path-filtered Terraform validation workflow.

Finally, I authored a Terraform AWS reference architecture — S3 data-lake layers with encryption/versioning/public-access-block, a Glue Data Catalog with separate Silver and Gold crawlers, an Athena workgroup with encrypted results, and least-privilege IAM roles. It is CI-validated with fmt, init, and validate, but deliberately never planned or applied, so it creates no resources or cost.

## Ten likely interview questions and answers

**1. Why the medallion (Bronze/Silver/Gold) architecture?**
It separates concerns cleanly: Bronze preserves raw source data for auditability and reprocessing, Silver applies cleaning and validation, and Gold delivers business-ready models. Each layer can be rebuilt independently, which makes debugging and backfills straightforward.

**2. Why keep everything as strings in Bronze?**
Casting too early risks silently dropping or corrupting malformed values. Keeping Bronze all-string preserves the raw input exactly, so validation and type-casting happen in Silver where I can control what to quarantine versus keep.

**3. How do you handle bad records — drop or fail the job?**
Neither. Records that fail business rules are routed to a quarantine path with a rejection reason and timestamp, so the pipeline keeps running while nothing is lost. Non-fatal issues (like a missing ZIP) are flagged with a data-quality column and retained.

**4. How is deduplication implemented?**
The Silver layer uses deterministic two-stage deduplication on business keys so results are reproducible across runs, rather than relying on non-deterministic ordering.

**5. What is SCD Type 2 and where is it used?**
Slowly Changing Dimension Type 2 keeps historical versions of a dimension over time. Providers can change attributes like network status, so Silver preserves each versioned provider row and the Gold dim_provider model carries the SCD2 history.

**6. Why dbt-duckdb instead of a warehouse load?**
DuckDB can query the Silver Parquet files directly, so dbt builds Gold with no separate ingestion step. That keeps the project fully local and reproducible while still demonstrating real dbt modeling and testing.

**7. How does your CI validate the whole repository?**
GitHub Actions runs parallel jobs: unit tests (ingestion, SQL, scripts), PySpark Silver tests on JDK 17, Airflow DAG tests after initializing the metadata DB, and a dbt parse check. A separate, path-filtered workflow validates Terraform with fmt, init, and validate.

**8. Why is the Terraform never applied?**
It is a reference architecture for the portfolio, not a live deployment. It is validated in CI (fmt/init/validate) so the configuration is provably sound, but plan/apply would need AWS credentials and would create real, billable resources — so it is intentionally never applied.

**9. How would this map to a real AWS deployment?**
The Terraform models it directly: S3 for the Bronze/Silver/Gold/quarantine/logs/results layers, Glue Data Catalog with Silver and Gold crawlers for schema discovery, Athena for serverless SQL, and least-privilege IAM roles for Glue and Athena. PySpark would run on Glue or EMR.

**10. What are the honest limitations?**
All data is synthetic. The Terraform is reference-only and never deployed (CI-validated only). Streaming is not implemented and remains optional future work.
