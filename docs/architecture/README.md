# docs/architecture/

Architecture documentation for ClaimsLake.

This folder will contain (added incrementally as milestones are built):

- `high_level_architecture.md` - end-to-end system diagram and component overview
- `data_flow.md` - detailed Bronze -> Silver -> Gold data flow
- `batch_pipeline.md` - batch pipeline design and scheduling
- `streaming_demo.md` - optional local Kafka streaming simulation design
- `ci_cd_flow.md` - GitHub Actions pipeline design
- `aws_reference_architecture.md` - AWS production design (S3, Glue, Redshift, IAM) vs. local implementation

Diagrams are provided as both source (draw.io / mermaid) and exported images in `docs/screenshots`.

## Silver layer architecture (Milestone 3)

```
SOURCE -> PYTHON INGESTION -> BRONZE -> PYSPARK SILVER -> (GOLD, later)
                                             |
                                             +--> QUARANTINE
```

The Silver stage is implemented in the `spark_jobs/` package (single
source of truth; see `spark_jobs/README.md`) and reads Bronze Parquet,
producing:

- `silver/<dataset>/` - cleaned, typed, deduplicated, validated data.
- `silver/quarantine/<dataset>/` - records that failed validation,
  retained with `rejection_reason` and `validation_timestamp`
  instead of being dropped.
- `data_quality/metrics/` - per-run JSON metrics computed from real
  execution.

Design highlights: explicit schemas (Bronze is all-string), two-stage
deterministic deduplication, PRESERVATION of provider historical versions
for future SCD Type 2, broadcast-join referential-integrity checks,
late-arriving claim flagging, claims batch-1/batch-2 schema normalization,
and date-based partitioning of the claims fact. Full rationale is in
`spark_jobs/README.md` and `docs/interview_guide/03_pyspark_silver.md`;
schemas are in `docs/data_dictionary/silver_schemas.md`; lineage is in
`docs/data_lineage/`.
