-- ============================================================================
-- ClaimsLake Analytics :: Data Quality Analytics
-- File: sql/data_quality/data_quality_analytics.sql
-- Engine: DuckDB (compatible with the Gold warehouse produced by dbt)
-- ----------------------------------------------------------------------------
-- These queries monitor the health of the ClaimsLake pipeline. They combine
-- the Gold warehouse (fact_claims, dim_provider) with the raw Silver-layer
-- quarantine Parquet files so analysts can see what data was rejected and why.
--
-- NOTE: Quarantine queries read Parquet directly and therefore MUST be run from
-- the repository root so the relative paths resolve, e.g.:
--   duckdb gold/claimslake.duckdb < sql/data_quality/data_quality_analytics.sql
-- ============================================================================


-- ----------------------------------------------------------------------------
-- Q31: Quarantined claims summary
-- Business question: How many claim records were rejected during ingestion,
--   and for which reasons?
-- Why it matters: Quarantine volume is the front-line signal of upstream data
--   quality problems. A spike in rejections usually means a partner changed
--   their file format or a mapping broke.
-- Expected output: One row per rejection_reason with a count, worst first.
-- ----------------------------------------------------------------------------
SELECT
    rejection_reason,
    COUNT(*) AS quarantined_records
FROM read_parquet('silver/quarantine/claims/**/*.parquet', union_by_name => true)
GROUP BY rejection_reason
ORDER BY quarantined_records DESC;


-- ----------------------------------------------------------------------------
-- Q32: Quarantine volume by dataset
-- Business question: Across every ingested dataset, where is data quality
--   failing the most?
-- Why it matters: Comparing quarantine volume across members, providers,
--   diagnoses and claims tells the platform team which source system needs
--   remediation first.
-- Expected output: One row per dataset with a total quarantined count.
-- ----------------------------------------------------------------------------
SELECT 'members'   AS dataset, COUNT(*) AS quarantined_records
FROM read_parquet('silver/quarantine/members/**/*.parquet', union_by_name => true)
UNION ALL
SELECT 'providers' AS dataset, COUNT(*) AS quarantined_records
FROM read_parquet('silver/quarantine/providers/**/*.parquet', union_by_name => true)
UNION ALL
SELECT 'diagnoses' AS dataset, COUNT(*) AS quarantined_records
FROM read_parquet('silver/quarantine/diagnoses/**/*.parquet', union_by_name => true)
UNION ALL
SELECT 'claims'    AS dataset, COUNT(*) AS quarantined_records
FROM read_parquet('silver/quarantine/claims/**/*.parquet', union_by_name => true)
ORDER BY quarantined_records DESC;


-- ----------------------------------------------------------------------------
-- Q33: Late-arriving claims
-- Business question: How many claims arrived after their service date window,
--   and how late were they on average?
-- Why it matters: Late-arriving claims distort monthly financial reporting and
--   accrual estimates. Payers track this to reserve funds for claims not yet
--   received (IBNR - incurred but not reported).
-- Expected output: Count of late claims, their share of all claims, and the
--   average / maximum lateness in days.
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*) FILTER (WHERE is_late_arriving)                    AS late_claims,
    COUNT(*)                                                    AS total_claims,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_late_arriving)
          / NULLIF(COUNT(*), 0), 2)                             AS late_pct,
    ROUND(AVG(days_late) FILTER (WHERE is_late_arriving), 1)    AS avg_days_late,
    MAX(days_late)                                              AS max_days_late
FROM fact_claims;


-- ----------------------------------------------------------------------------
-- Q34: Duplicate NPIs
-- Business question: Are there National Provider Identifiers shared by more
--   than one provider record?
-- Why it matters: An NPI is meant to uniquely identify a provider. Duplicates
--   indicate identity-resolution problems that can cause misattributed claims
--   and compliance issues.
-- Expected output: One row per NPI used by multiple providers, with the count
--   of distinct provider_ids sharing it.
-- ----------------------------------------------------------------------------
SELECT
    npi,
    COUNT(DISTINCT provider_id) AS distinct_providers
FROM dim_provider
WHERE npi IS NOT NULL
GROUP BY npi
HAVING COUNT(DISTINCT provider_id) > 1
ORDER BY distinct_providers DESC;


-- ----------------------------------------------------------------------------
-- Q35: Missing specialties
-- Business question: How many current providers are missing a specialty value?
-- Why it matters: Specialty drives network adequacy analysis and claim routing.
--   Missing specialties reduce the reliability of provider-based analytics and
--   must be back-filled from the source system.
-- Expected output: Count and percentage of current providers with no specialty.
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*) FILTER (WHERE specialty IS NULL OR TRIM(specialty) = '') AS missing_specialty,
    COUNT(*)                                                          AS current_providers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE specialty IS NULL OR TRIM(specialty) = '')
          / NULLIF(COUNT(*), 0), 2)                                   AS missing_specialty_pct
FROM dim_provider
WHERE is_current;
