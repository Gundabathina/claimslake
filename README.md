# ClaimsLake — Healthcare Claims Data Engineering Platform

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
Gold Layer (dbt + SQL: star schema — fact_claims, dim_member, dim_provider (SCD2), dim_diagnosis, dim_date)
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
├── docs/                 architecture, data dictionary, lineage, interview guide, screenshots
├── data/                 sample synthetic data
├── ingestion/            Python ingestion scripts
├── processing/           bronze / silver / gold processing code
├── pyspark/              PySpark transformation jobs
├── airflow/dags/         Airflow DAG definitions
├── dbt/                  dbt project (staging, marts, tests)
├── sql/                  DDL and analytical SQL
├── streaming/            optional local Kafka demo
├── tests/                pytest unit and data quality tests
├── terraform/            AWS reference infrastructure as code
├── docker/               Dockerfiles
├── scripts/              helper/dev scripts
└── config/               pipeline configuration
```

## Project status / roadmap

- [x] Milestone 0 — Repository scaffolding
- [x] Milestone 1 — Synthetic data generation
- [ ] Milestone 2 — Python ingestion layer (Bronze)
- [ ] Milestone 3 — PySpark Silver transformations
- [ ] Milestone 4 — Gold star schema via dbt
- [ ] Milestone 5 — Analytical SQL layer
- [ ] Milestone 6 — Airflow orchestration
- [ ] Milestone 7 — Testing suite
- [ ] Milestone 8 — Docker Compose full stack
- [ ] Milestone 9 — GitHub Actions CI/CD
- [ ] Milestone 10 — Terraform AWS reference architecture
- [ ] Milestone 11 — Optional Kafka streaming demo
- [ ] Milestone 12 — Full documentation
- [ ] Milestone 13 — Interview guide

## Honesty note

This is a personal portfolio project built with synthetic data to demonstrate data engineering skills. It does not represent real employment experience, a real company's data, or a live production deployment. Any AWS architecture described is a documented reference design implemented via Terraform; cloud resources are not kept running live to avoid unnecessary cost. See `docs/interview_guide` for a full, honest breakdown of what was actually run versus simulated.

## License

MIT — see [LICENSE](LICENSE).
