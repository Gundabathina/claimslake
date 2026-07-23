# ClaimsLake â Healthcare Claims Data Engineering Platform

**Status:** Actively under construction (portfolio project, built incrementally in public commits). This README is updated at every milestone.

An end-to-end, production-style data engineering platform that ingests, cleans, models, and analyzes **synthetic** healthcare claims data using a medallion (Bronze/Silver/Gold) architecture.

## Why this project exists

Health insurers and providers process huge volumes of claims data every day, arriving messy, duplicated, and inconsistent across source systems. Analysts need trustworthy, well-modeled data to answer questions such as which providers have the highest denial rates, which diagnoses drive the most cost, and whether processing times are degrading. ClaimsLake demonstrates how a data engineer would build the pipeline that turns raw claims data into analytics-ready tables.

**All data used in this project is synthetic**, generated to resemble realistic healthcare claims structures (similar in spirit to CMS synthetic public-use files and the Synthea patient generator). No real patient, member, or provider data is used anywhere in this repository.

## Architecture (high level)

```
Synthetic Data Generators (members, providers, diagnoses, claims)
        |
        v
Python Ingestion Layer (full + incremental load, retries, logging)
        |
        v
Bronze Layer (raw Parquet, partitioned by ingestion date)
        |
        v
Data Quality & Validation checks
        |
        v
Silver Layer (PySpark: cleaned, deduplicated, standardized)
        |
        v
Gold Layer (dbt + SQL: star schema â fact_claims, dim_member, dim_provider (SCD2), dim_diagnosis, dim_date)
        |
        v
Analytics Warehouse (DuckDB/Postgres locally; Redshift design for AWS)
        |
        v
BI / analytical SQL queries

Orchestration: Apache Airflow coordinates every stage above.
CI/CD: GitHub Actions runs lint, unit tests, and dbt tests on every push.
```

Full architecture diagrams and data lineage docs live in [`docs/architecture`](docs/architecture) and [`docs/data_lineage`](docs/data_lineage).

## Technology stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.11 | Ingestion, utilities, tests |
| Processing | PySpark | Bronze to Silver to Gold transformations |
| Lake storage | Parquet (local), MinIO (S3-compatible) | Columnar storage, local S3 simulation |
| Orchestration | Apache Airflow (Docker) | DAG scheduling, retries, dependencies |
| Transformation/modeling | dbt | Gold-layer star schema, tests, docs |
| Local warehouse | DuckDB / Postgres | Stand-in for a cloud warehouse |
| AWS reference design | S3, Glue, Redshift, IAM (Terraform, documented) | Production-scale cloud architecture |
| Containerization | Docker & Docker Compose | Reproducible local environment |
| IaC | Terraform | AWS resource definitions (not auto-deployed) |
| CI/CD | GitHub Actions | Lint, tests, dbt tests, build validation |
| Testing | pytest, dbt tests | Unit and data quality testing |
| Streaming (optional demo) | Kafka (local Docker) | Local simulation of real-time claim events, clearly labeled as non-production |

## Repository structure

```
claimslake/
âââ docs/                 architecture, data dictionary, lineage, interview guide, screenshots
âââ data/                 sample synthetic data
âââ ingestion/            Python ingestion scripts
âââ processing/           bronze / silver / gold processing code
âââ spark_jobs/              PySpark transformation jobs
âââ airflow/dags/         Airflow DAG definitions
âââ dbt/                  dbt project (staging, marts, tests)
âââ sql/                  DDL and analytical SQL
âââ streaming/            optional local Kafka demo
âââ tests/                pytest unit and data quality tests
âââ terraform/            AWS reference infrastructure as code
âââ docker/               Dockerfiles
âââ scripts/              helper/dev scripts
âââ config/               pipeline configuration
```

## Project status / roadmap

- [x] Milestone 0 â Repository scaffolding
- [x] Milestone 1 â Synthetic data generation
- [x] Milestone 2 â Python ingestion layer (Bronze)
- [x] Milestone 3 â PySpark Silver transformations
- [ ] Milestone 4 â Gold star schema via dbt
- [ ] Milestone 5 â Analytical SQL layer
- [ ] Milestone 6 â Airflow orchestration
- [ ] Milestone 7 â Testing suite
- [ ] Milestone 8 â Docker Compose full stack
- [ ] Milestone 9 â GitHub Actions CI/CD
- [ ] Milestone 10 â Terraform AWS reference architecture
- [ ] Milestone 11 â Optional Kafka streaming demo
- [ ] Milestone 12 â Full documentation
- [ ] Milestone 13 â Interview guide

## Running the ingestion layer (Milestone 2)

```bash
pip install -r requirements.txt
python -m ingestion.src.ingestion_engine --all   # load all sources into Bronze
pytest tests/ingestion -v                         # run the ingestion tests
```

The Bronze ingestion framework is configuration-driven and demonstrates full/incremental loads, idempotency (SHA-256 file hashing), retry logic, schema-drift detection, structured logging, and a SQLite ingestion audit log. It preserves source data faithfully in Bronze (Parquet, partitioned by ingestion date) and performs no business transformation. See ingestion/README.md for the full design and docs/interview_guide/02_ingestion_bronze.md for interview Q&A. All data is synthetic.

## Running the Silver layer (Milestone 3)

```bash
pip install -r requirements.txt
python -m ingestion.src.ingestion_engine --all   # SOURCE -> BRONZE
python -m spark_jobs.src.silver_pipeline --all        # BRONZE -> SILVER
pytest tests/pyspark -v                            # run the PySpark tests
```

The PySpark Silver layer reads Bronze Parquet and produces cleaned, typed, deduplicated, validated datasets under `silver/`, quarantining invalid records (with reasons) under `silver/quarantine/` rather than dropping them, and writing data-quality metrics to `data_quality/metrics/`. It preserves provider historical versions so the Gold layer can later build an SCD Type 2 dimension, normalizes the claims_batch_1/claims_batch_2 schemas, flags late-arriving claims, and checks referential integrity with broadcast joins. Requires a JVM (Java 11/17) for Spark. See spark_jobs/README.md for the full design and docs/interview_guide/03_pyspark_silver.md for interview Q&A. All data is synthetic.

## Honesty note

This is a personal portfolio project built with synthetic data to demonstrate data engineering skills. It does not represent real employment experience, a real company's data, or a live production deployment. Any AWS architecture described is a documented reference design implemented via Terraform; cloud resources are not kept running live to avoid unnecessary cost. See `docs/interview_guide` for a full, honest breakdown of what was actually run versus simulated.

## License

MIT â see [LICENSE](LICENSE).
