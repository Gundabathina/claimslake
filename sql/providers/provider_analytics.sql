-- =====================================================================
-- ClaimsLake  |  Provider Analytics
-- =====================================================================
-- Warehouse : gold/claimslake.duckdb
-- Table     : dim_provider (SCD Type 2)
--   provider_sk, provider_id, provider_name, specialty, npi,
--   network_status, address_state, effective_date, valid_from,
--   valid_to, is_current
--   fact_claims (provider_id, provider_specialty, network_status, ...)
-- Run       : duckdb gold/claimslake.duckdb < sql/providers/provider_analytics.sql
-- =====================================================================


-- ---------------------------------------------------------------------
-- Q26. Providers by specialty
-- Business question: How many (current) providers practice each specialty?
-- Why it matters: Specialty coverage is the core of network-adequacy
--   analysis and regulatory access standards.
-- Expected output: one row per specialty, most providers first.
-- Restrict to is_current to count each provider once (SCD2 has history).
-- ---------------------------------------------------------------------
select
    coalesce(specialty, '(unknown)') as specialty,
    count(*)                          as provider_count
from dim_provider
where is_current = true
group by specialty
order by provider_count desc;


-- ---------------------------------------------------------------------
-- Q27. Network vs out-of-network
-- Business question: How many current providers are in-network vs not?
-- Why it matters: In-network share drives member out-of-pocket exposure
--   and steerage strategy.
-- Expected output: one row per network_status.
-- ---------------------------------------------------------------------
select
    network_status,
    count(*)   as provider_count
from dim_provider
where is_current = true
group by network_status
order by provider_count desc;


-- ---------------------------------------------------------------------
-- Q28. Active providers
-- Business question: How many distinct active (current) providers exist?
-- Why it matters: The size of the usable network at a point in time.
-- Expected output: single row, one integer.
-- ---------------------------------------------------------------------
select count(distinct provider_id) as active_providers
from dim_provider
where is_current = true;


-- ---------------------------------------------------------------------
-- Q29. Provider historical versions (SCD Type 2)
-- Business question: Which providers have multiple historical versions,
--   and how do their valid_from / valid_to windows look?
-- Why it matters: SCD2 lets us attribute each claim to the provider
--   attributes (e.g. network status) that were correct on the service
--   date - essential for accurate, auditable analytics.
-- Expected output: providers with >1 version, one row per version, with
--   validity window and is_current flag.
-- ---------------------------------------------------------------------
with version_counts as (
    select provider_id, count(*) as version_count
    from dim_provider
    group by provider_id
    having count(*) > 1
)
select
    dp.provider_id,
    dp.provider_name,
    dp.network_status,
    dp.valid_from,
    dp.valid_to,
    dp.is_current
from dim_provider dp
join version_counts vc on dp.provider_id = vc.provider_id
order by dp.provider_id, dp.valid_from;


-- ---------------------------------------------------------------------
-- Q30. Top specialties by claim volume
-- Business question: Which specialties generate the most claims?
-- Why it matters: Links network composition to actual utilization and
--   spend, guiding contracting priorities.
-- Expected output: one row per specialty, highest claim volume first.
-- Uses provider_specialty carried on the fact for the current version.
-- ---------------------------------------------------------------------
select
    coalesce(provider_specialty, '(unknown)') as specialty,
    count(*)                                   as claim_count,
    round(sum(paid_amount), 2)                 as total_paid
from fact_claims
group by provider_specialty
order by claim_count desc;
