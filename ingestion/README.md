# ingestion/

Python ingestion layer: reads source files (synthetic members, providers, diagnoses, claims) and loads them into the Bronze layer.

Demonstrates (built in Milestone 2):

- Full load and incremental load modes, driven by config
- Retry logic with backoff for transient failures
- Structured logging
- Ingestion metadata tracking (row counts, batch id, source file, load timestamp) for auditability and idempotency
- Config-driven source definitions (see `config/`)
