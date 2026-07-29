-- =====================================================================
-- ClaimsLake  |  Claims Analytics
-- =====================================================================
-- Warehouse : gold/claimslake.duckdb  (dbt-duckdb Gold star schema)
-- Tables    : fact_claims (grain = one row per claim_id)
--             dim_member, dim_provider (SCD2)
-- Run       : duckdb gold/claimslake.duckdb < sql/claims/claims_analytics.sql
-- Every query below uses only real Gold columns.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Q1. Total claims
-- Business question: How many claims are in the warehouse overall?
-- Why it matters: The denominator for every rate metric and a basic
--   volume KPI payers watch to size operational load.
-- Expected output: single row, one integer (total claim count).
-- ---------------------------------------------------------------------
select count(*) as total_claims
from fact_claims;


-- ---------------------------------------------------------------------
-- Q2. Paid claims
-- Business question: How many claims were paid (not denied)?
-- Why it matters: Paid volume drives cash outflow and provider
--   reimbursement timeliness.
-- Expected output: single row, one integer.
-- ---------------------------------------------------------------------
select count(*) as paid_claims
from fact_claims
where lower(claim_status) = 'paid';


-- ---------------------------------------------------------------------
-- Q3. Denied claims
-- Business question: How many claims were denied?
-- Why it matters: Denials create rework, provider abrasion, and member
--   dissatisfaction; a core operational quality signal.
-- Expected output: single row, one integer.
-- is_denied is a precomputed Gold flag (1 when claim_status = 'denied').
-- ---------------------------------------------------------------------
select sum(is_denied) as denied_claims
from fact_claims;


-- ---------------------------------------------------------------------
-- Q4. Denial percentage
-- Business question: What share of claims are denied?
-- Why it matters: Denial rate is a headline healthcare KPI; >10% often
--   signals eligibility, coding, or authorization problems.
-- Expected output: single row with denied_claims, total_claims, denial_pct.
-- ---------------------------------------------------------------------
select
    sum(is_denied)                                   as denied_claims,
    count(*)                                          as total_claims,
    round(100.0 * sum(is_denied) / count(*), 2)       as denial_pct
from fact_claims;


-- ---------------------------------------------------------------------
-- Q5. Monthly claim trend
-- Business question: How does claim volume move month over month?
-- Why it matters: Seasonality and spikes inform staffing and detect
--   anomalies (e.g. a bad feed or an outbreak).
-- Expected output: one row per service_year_month, ordered chronologically.
-- ---------------------------------------------------------------------
select
    service_year_month,
    count(*)              as claim_count,
    sum(is_denied)        as denied_claims
from fact_claims
group by service_year_month
order by service_year_month;


-- ---------------------------------------------------------------------
-- Q6. Claims by state
-- Business question: Where (member state) do claims originate?
-- Why it matters: Geographic concentration guides network adequacy and
--   regional cost management.
-- Expected output: one row per member_state, highest volume first.
-- ---------------------------------------------------------------------
select
    member_state,
    count(*)         as claim_count,
    sum(is_denied)   as denied_claims
from fact_claims
group by member_state
order by claim_count desc;


-- ---------------------------------------------------------------------
-- Q7. Claims by diagnosis
-- Business question: Which diagnosis codes drive the most claims?
-- Why it matters: High-frequency diagnoses reveal population health
--   burden and care-management opportunities.
-- Expected output: one row per diagnosis_code, highest volume first.
-- ---------------------------------------------------------------------
select
    diagnosis_code,
    count(*)   as claim_count
from fact_claims
group by diagnosis_code
order by claim_count desc;


-- ---------------------------------------------------------------------
-- Q8. Claims by provider
-- Business question: How many claims does each provider submit?
-- Why it matters: Volume per provider supports contracting, capacity,
--   and outlier/fraud detection.
-- Expected output: one row per provider_id, highest volume first.
-- ---------------------------------------------------------------------
select
    provider_id,
    count(*)   as claim_count
from fact_claims
group by provider_id
order by claim_count desc;


-- ---------------------------------------------------------------------
-- Q9. Claims by specialty
-- Business question: Which provider specialties generate the most claims?
-- Why it matters: Specialty mix shapes cost trends and network design.
-- Expected output: one row per provider_specialty, highest volume first.
-- provider_specialty is carried on fact_claims from the current provider
-- version at build time.
-- ---------------------------------------------------------------------
select
    coalesce(provider_specialty, '(unknown)') as provider_specialty,
    count(*)                                   as claim_count
from fact_claims
group by provider_specialty
order by claim_count desc;


-- ---------------------------------------------------------------------
-- Q10. Top 10 providers by volume
-- Business question: Who are the ten highest-volume providers?
-- Why it matters: Top providers concentrate spend and operational risk;
--   they are prime candidates for value-based contracts and audits.
-- Expected output: up to 10 rows (provider_id, provider name, claim_count).
-- Joins to dim_provider current version for a human-readable name.
-- ---------------------------------------------------------------------
select
    f.provider_id,
    dp.provider_name,
    count(*)   as claim_count
from fact_claims f
left join dim_provider dp
       on f.provider_id = dp.provider_id
      and dp.is_current = true
group by f.provider_id, dp.provider_name
order by claim_count desc
limit 10;
