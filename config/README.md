# config/

Pipeline configuration (YAML/JSON), kept separate from code so ingestion sources, file paths, and pipeline behavior can change without editing Python.

Will include (Milestone 2): source definitions per entity (member/provider/diagnosis/claim), load mode (full vs incremental), retry settings, and environment-specific overrides. No secrets are ever stored here — secrets come from `.env` (gitignored) or environment variables, never committed config files.
