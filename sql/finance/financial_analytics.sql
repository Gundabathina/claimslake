-- =====================================================================
-- ClaimsLake  |  Financial Analytics
-- =====================================================================
-- Warehouse : gold/claimslake.duckdb
-- Table     : fact_claims  (billed_amount, paid_amount, unpaid_amount)
-- Run       : duckdb gold/claimslake.duckdb < sql/finance/financial_analytics.sql
--
-- NOTE ON "ADJUSTMENTS": the Gold star schema does not expose a raw
-- adjustment_amount column. The economically meaningful adjustment is the
-- amount billed but NOT paid, which the Gold layer already materialises as
-- unpaid_amount = billed_amount - paid_amount. We use that real column and
-- label it honestly rather than inventing a column.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Q11. Total billed amount
-- Business question: What is the total dollar amount providers billed?
-- Why it matters: Gross billed is the top of the revenue-cycle funnel and
--   the basis for contractual discount analysis.
-- Expected output: single row, one numeric total.
-- ---------------------------------------------------------------------
select round(sum(billed_amount), 2) as total_billed_amount
from fact_claims;


-- ---------------------------------------------------------------------
-- Q12. Total paid amount
-- Business question: What did the payer actually pay out?
-- Why it matters: Total paid is real cash outflow and the core of medical
--   loss ratio (MLR) calculations.
-- Expected output: single row, one numeric total.
-- ---------------------------------------------------------------------
select round(sum(paid_amount), 2) as total_paid_amount
from fact_claims;


-- ---------------------------------------------------------------------
-- Q13. Total adjustments (billed not paid)
-- Business question: How much of billed charges were not paid?
-- Why it matters: The billed-to-paid gap reflects contractual write-offs,
--   denials, and member responsibility - a key leakage metric.
-- Expected output: single row, one numeric total (sum of unpaid_amount).
-- ---------------------------------------------------------------------
select round(sum(unpaid_amount), 2) as total_adjustments_billed_not_paid
from fact_claims;


-- ---------------------------------------------------------------------
-- Q14. Average paid amount
-- Business question: What is the mean paid amount per claim?
-- Why it matters: Average paid per claim trends drive premium pricing and
--   detect cost inflation.
-- Expected output: single row, one numeric average.
-- ---------------------------------------------------------------------
select round(avg(paid_amount), 2) as avg_paid_amount
from fact_claims;


-- ---------------------------------------------------------------------
-- Q15. Average billed amount
-- Business question: What is the mean billed amount per claim?
-- Why it matters: Benchmarks provider charge levels vs. peers and helps
--   spot upcoding.
-- Expected output: single row, one numeric average.
-- ---------------------------------------------------------------------
select round(avg(billed_amount), 2) as avg_billed_amount
from fact_claims;


-- ---------------------------------------------------------------------
-- Q16. Monthly paid trend
-- Business question: How does total paid move month over month?
-- Why it matters: Cash-flow forecasting and reserve setting.
-- Expected output: one row per service_year_month, chronological.
-- ---------------------------------------------------------------------
select
    service_year_month,
    round(sum(paid_amount), 2) as total_paid
from fact_claims
group by service_year_month
order by service_year_month;


-- ---------------------------------------------------------------------
-- Q17. Monthly billed trend
-- Business question: How does total billed move month over month?
-- Why it matters: Tracks provider charge volume and seasonality.
-- Expected output: one row per service_year_month, chronological.
-- ---------------------------------------------------------------------
select
    service_year_month,
    round(sum(billed_amount), 2) as total_billed
from fact_claims
group by service_year_month
order by service_year_month;


-- ---------------------------------------------------------------------
-- Q18. Cost per diagnosis
-- Business question: Which diagnoses cost the most in paid dollars?
-- Why it matters: Directs care-management and cost-containment programs
--   at the most expensive condition groups.
-- Expected output: one row per diagnosis_code, highest paid first.
-- ---------------------------------------------------------------------
select
    diagnosis_code,
    count(*)                    as claim_count,
    round(sum(paid_amount), 2)  as total_paid
from fact_claims
group by diagnosis_code
order by total_paid desc;


-- ---------------------------------------------------------------------
-- Q19. Cost per provider
-- Business question: Which providers account for the most paid dollars?
-- Why it matters: Spend concentration informs contracting and audit focus.
-- Expected output: one row per provider_id, highest paid first.
-- ---------------------------------------------------------------------
select
    provider_id,
    count(*)                    as claim_count,
    round(sum(paid_amount), 2)  as total_paid
from fact_claims
group by provider_id
order by total_paid desc;


-- ---------------------------------------------------------------------
-- Q20. Top 10 most expensive diagnoses (by average paid)
-- Business question: Which diagnoses have the highest average paid per
--   claim (not just total volume)?
-- Why it matters: High per-claim cost conditions are targets for case
--   management and reinsurance planning.
-- Expected output: up to 10 rows, highest avg_paid first.
-- HAVING guards against tiny-sample noise.
-- ---------------------------------------------------------------------
select
    diagnosis_code,
    count(*)                    as claim_count,
    round(avg(paid_amount), 2)  as avg_paid
from fact_claims
group by diagnosis_code
having count(*) >= 1
order by avg_paid desc
limit 10;
