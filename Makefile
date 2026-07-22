# ClaimsLake — developer convenience commands
# Usage: make <target>

.PHONY: help up down logs generate-data ingest test lint dbt-run dbt-test airflow-up clean

help:
	@echo "ClaimsLake Makefile targets:"
	@echo "  up             - Start local stack (MinIO, Postgres, Airflow) via Docker Compose"
	@echo "  down           - Stop local stack"
	@echo "  logs           - Tail logs from all running containers"
	@echo "  generate-data  - Generate synthetic source data"
	@echo "  ingest         - Run ingestion scripts (Bronze load)"
	@echo "  test           - Run pytest unit and data quality tests"
	@echo "  lint           - Run code linters"
	@echo "  dbt-run        - Run dbt models (Gold layer)"
	@echo "  dbt-test       - Run dbt tests"
	@echo "  airflow-up     - Start only the Airflow webserver+scheduler"
	@echo "  clean          - Remove local containers, volumes, and caches"

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

generate-data:
	python scripts/generate_synthetic_data.py

ingest:
	python ingestion/run_ingestion.py

test:
	pytest tests/ -v

lint:
	python -m flake8 ingestion pyspark tests scripts

dbt-run:
	cd dbt && dbt run

dbt-test:
	cd dbt && dbt test

airflow-up:
	docker compose up -d airflow-webserver airflow-scheduler

clean:
	docker compose down -v --remove-orphans
	find . -type d -name "__pycache__" -exec rm -rf {} +
