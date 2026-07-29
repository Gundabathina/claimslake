-- =====================================================================
-- ClaimsLake :: Member Analytics
-- =====================================================================
-- Warehouse : gold/claimslake.duckdb
-- Run       : duckdb gold/claimslake.duckdb < sql/members/member_analytics.sql
-- Real Gold columns:
--   dim_member(member_id, plan_type, state, zip_code, gender,
--     date_of_birth, has_missing_zip, source_system)
--   fact_claims(member_id, ...)  -- one row per claim_id
-- =====================================================================


-- ---------------------------------------------------------------------
-- 21. Members by state
-- Business question: How is the membership distributed geographically?
-- Expected output: one row per state, highest membership first.
-- Why it matters: drives network adequacy and regional benefit design.
-- ---------------------------------------------------------------------
select
    state,
    count(*) as members
from dim_member
group by state
order by members desc;


-- ---------------------------------------------------------------------
-- 22. Claims per member
-- Business question: How many claims does each member generate?
-- Expected output: one row per member_id with a claim count, busiest first.
-- Why it matters: high-utilizers are candidates for care management.
-- ---------------------------------------------------------------------
select
    member_id,
    count(*) as claim_count
from fact_claims
group by member_id
order by claim_count desc;


-- ---------------------------------------------------------------------
-- 23. Top members by utilization
-- Business question: Which members drive the most cost and volume?
-- Expected output: up to 20 members ranked by paid dollars.
-- Why it matters: a small share of members usually drives most spend;
-- these are the priority list for case management.
-- ---------------------------------------------------------------------
select
    member_id,
    count(*)                   as claim_count,
    round(sum(paid_amount), 2) as total_paid
from fact_claims
group by member_id
order by total_paid desc
limit 20;


-- ---------------------------------------------------------------------
-- 24. Member age distribution
-- Business question: What is the age profile of the membership?
-- Expected output: one row per 10-year age band with member counts.
-- Why it matters: age mix drives expected utilization and risk scoring.
-- Uses the real date_of_birth column; NULL DOBs fall into 'unknown'.
-- ---------------------------------------------------------------------
select
    case
        when date_of_birth is null then 'unknown'
        else cast((date_diff('year', date_of_birth, current_date) / 10) * 10 as varchar)
             || '-' ||
             cast((date_diff('year', date_of_birth, current_date) / 10) * 10 + 9 as varchar)
    end as age_band,
    count(*) as members
from dim_member
group by age_band
order by age_band;


-- ---------------------------------------------------------------------
-- 25. Average claims per member
-- Business question: On average, how many claims does a member file?
-- Expected output: one numeric average (claims / distinct members).
-- Why it matters: a population-level utilization baseline for trending.
-- ---------------------------------------------------------------------
select
    round(count(*) * 1.0 / count(distinct member_id), 2) as avg_claims_per_member
from fact_claims;
