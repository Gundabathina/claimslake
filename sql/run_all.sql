-- ============================================================================
-- ClaimsLake Analytics :: Master Runner
-- File: sql/run_all.sql
-- Engine: DuckDB
-- ----------------------------------------------------------------------------
-- Executes every analytical query in the ClaimsLake analytics layer against the
-- Gold warehouse. The data-quality queries read Silver-layer quarantine Parquet
-- via relative paths, so this script MUST be run from the repository ROOT:
--
--   duckdb gold/claimslake.duckdb < sql/run_all.sql
--
-- Each '.read' below sources one analytics file. DuckDB resolves these paths
-- relative to the current working directory (the repo root).
-- ============================================================================

.print '================ ClaimsLake Analytics :: Claims ================'
.read sql/claims/claims_analytics.sql

.print '================ ClaimsLake Analytics :: Providers =============='
.read sql/providers/provider_analytics.sql

.print '================ ClaimsLake Analytics :: Members ================'
.read sql/members/member_analytics.sql

.print '================ ClaimsLake Analytics :: Finance ==============='
.read sql/finance/financial_analytics.sql

.print '================ ClaimsLake Analytics :: Data Quality =========='
.read sql/data_quality/data_quality_analytics.sql

.print '================ ClaimsLake Analytics :: Complete =============='
