# Silver Data Dictionary - ClaimsLake

Canonical Silver schemas produced by `spark_jobs/src` (Milestone 3). All
data is synthetic. Bronze source schemas are in `source_schemas.md`;
Silver adds real types, standardization, validation, and lineage columns.
Bronze stores everything as strings, so all types below are the result of
casting in `cleaners.py`.

## silver/members (grain: one row per member_id)
| Column | Type | Notes |
| --- | --- | --- |
| member_id | string | business key |
| first_name, last_name | string | |
| date_of_birth | date | future dates quarantined |
| gender | string | trimmed, upper-cased |
| enrollment_start_date, enrollment_end_date | date | end may be null (active) |
| plan_type | string | |
| state | string | trimmed/upper; must be a valid US code |
| zip_code | string | may be null (flagged, not rejected) |
| source_system | string | |
| has_missing_zip | boolean | data-quality flag |
| ingestion_timestamp, source_file, file_hash | string | Bronze lineage, carried through |
| bronze_ingestion_date | string | source Bronze partition |

## silver/providers (grain: one row per (provider_id, effective_date) VERSION)
| Column | Type | Notes |
| --- | --- | --- |
| provider_id | string | NOT unique by itself - history preserved |
| provider_name | string | |
| specialty | string | may be null (flagged) |
| npi | string | |
| network_status | string | trimmed/upper; changes over time (SCD2 signal) |
| address_state | string | must be a valid US code |
| effective_date | date | version date; part of the grain |
| source_system | string | |
| has_missing_specialty | boolean | flag |
| has_duplicate_npi | boolean | flag: same NPI on multiple provider_ids |
| ingestion_timestamp, source_file, file_hash, bronze_ingestion_date | string | lineage |

Providers keep every distinct version so Gold can build SCD Type 2
(`valid_from`/`valid_to`/`is_current`). Silver does not compute
those columns.

## silver/diagnoses (grain: one row per diagnosis_code)
| Column | Type | Notes |
| --- | --- | --- |
| diagnosis_code | string | business key, trimmed/upper |
| diagnosis_description | string | |
| category | string | |
| ingestion_timestamp, source_file, file_hash, bronze_ingestion_date | string | lineage |

## silver/claims (grain: one row per claim_id; partitioned by service_year_month)
| Column | Type | Notes |
| --- | --- | --- |
| claim_id | string | business key |
| member_id | string | FK -> members (validated) |
| provider_id | string | FK -> providers (validated) |
| diagnosis_code | string | FK -> diagnoses (validated), trimmed/upper |
| service_date | date | |
| submission_date | date | must be >= service_date |
| billed_amount | decimal(12,2) | |
| paid_amount | decimal(12,2) | may be null (Pending/Denied); negative rejected |
| claim_status | string | Paid / Denied / Pending |
| denial_reason | string | null unless Denied |
| ingestion_batch_id | string | BATCH_1 / BATCH_2 |
| source_system | string | |
| adjustment_amount | decimal(12,2) | canonical; null for batch_1 rows |
| is_late_arriving | boolean | submission - service > 45 days |
| days_late | int | null if dates missing |
| service_year_month | string | partition column, derived from service_date |
| ingestion_timestamp, source_file, file_hash | string | lineage |

## silver/quarantine/<dataset> (rejected records)
Every quarantined record keeps all of its original (cleaned) columns plus:
| Column | Type | Notes |
| --- | --- | --- |
| rejection_reason | string | one or more reasons, joined by "; " |
| validation_timestamp | timestamp | when the record was rejected |

Rejection reasons include: `invalid_state_code`,
`impossible_date_of_birth_future`, `invalid_address_state`,
`missing_effective_date`, `negative_paid_amount`,
`missing_paid_amount_for_paid_claim`, `submission_before_service_date`,
`invalid_or_missing_date`, `invalid_claim_status`, and the
referential-integrity reasons `invalid_member_id_reference`,
`invalid_provider_id_reference`, `invalid_diagnosis_code_reference`.
