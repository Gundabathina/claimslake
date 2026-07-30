# ClaimsLake Analytics Catalog

This catalog documents the Stage 4 analytics SQL layer. Every query runs on the
Gold warehouse (`gold/claimslake.duckdb`) produced by the dbt marts, using only
real Gold tables and columns. There are **35 queries** across five domains.

## How to run

All analytics run in DuckDB from the **repository root** (the data-quality
queries read Silver quarantine Parquet via relative paths):

```bash
# Run everything
duckdb gold/claimslake.duckdb < sql/run_all.sql

# Run a single domain
duckdb gold/claimslake.duckdb < sql/claims/claims_analytics.sql
```

## Gold schema used by these queries

| Table | Grain | Key columns used |
|-------|-------|------------------|
| `fact_claims` | one row per claim_id | claim_status, is_denied, billed_amount, paid_amount, unpaid_amount, service_year_month, member_state, diagnosis_code, provider_id, provider_specialty, is_late_arriving, days_late |
| `dim_member` | one row per member | member_id, state, date_of_birth |
| `dim_provider` (SCD2) | one row per provider version | provider_id, provider_sk, specialty, npi, network_status, is_current, valid_from, valid_to |

> Note: `fact_claims` carries no `adjustment_amount`; "Total adjustments" is
> modelled as the billed amount not paid (`unpaid_amount = billed - paid`).

---

## Claims Analytics — `sql/claims/claims_analytics.sql` (Q1–Q10)

| # | Query | Business purpose | Expected result | Healthcare interpretation |
|---|-------|------------------|-----------------|---------------------------|
| Q1 | Total claims | Baseline volume | Single count of all claims | The denominator for every rate metric |
| Q2 | Paid claims | Adjudication outcome | Count where status = paid | Share of claims that reimbursed |
| Q3 | Denied claims | Adjudication outcome | Count where denied | Denials drive appeals and provider abrasion |
| Q4 | Denial percentage | Quality/efficiency KPI | Denied / total as % | A headline payer-operations KPI |
| Q5 | Monthly claim trend | Volume over time | Count per service_year_month | Surfaces seasonality and data gaps |
| Q6 | Claims by state | Geographic mix | Count per member_state | Network adequacy by region |
| Q7 | Claims by diagnosis | Clinical mix | Count per diagnosis_code | Reveals dominant conditions |
| Q8 | Claims by provider | Provider volume | Count per provider_id | Utilization concentration |
| Q9 | Claims by specialty | Specialty mix | Count per provider_specialty | Care-setting distribution |
| Q10 | Top 10 providers by volume | High-volume providers | Ranked top 10 | Contracting & audit focus list |

## Financial Analytics — `sql/finance/financial_analytics.sql` (Q11–Q20)

| # | Query | Business purpose | Expected result | Healthcare interpretation |
|---|-------|------------------|-----------------|---------------------------|
| Q11 | Total billed amount | Gross exposure | Sum of billed_amount | Provider-charged total |
| Q12 | Total paid amount | Net spend | Sum of paid_amount | What the plan actually paid |
| Q13 | Total adjustments | Billed not paid | Sum of unpaid_amount | Contractual write-offs & denials |
| Q14 | Average paid amount | Unit cost | Mean paid per claim | Cost-per-claim benchmark |
| Q15 | Average billed amount | Unit charge | Mean billed per claim | Charge-master benchmark |
| Q16 | Monthly paid trend | Spend over time | Sum paid per month | Budget & trend monitoring |
| Q17 | Monthly billed trend | Charges over time | Sum billed per month | Exposure trend |
| Q18 | Cost per diagnosis | Clinical cost driver | Sum paid per diagnosis | Where the money goes clinically |
| Q19 | Cost per provider | Provider cost driver | Sum paid per provider | High-cost provider identification |
| Q20 | Top expensive diagnoses | Cost concentration | Top diagnoses by avg paid | Case-management targeting |

## Member Analytics — `sql/members/member_analytics.sql` (Q21–Q25)

| # | Query | Business purpose | Expected result | Healthcare interpretation |
|---|-------|------------------|-----------------|---------------------------|
| Q21 | Members by state | Geographic distribution | Count per state | Network adequacy & benefit design |
| Q22 | Claims per member | Utilization per member | Count per member_id | Identifies high-utilizers |
| Q23 | Top members by utilization | Cost concentration | Top 20 by paid dollars | Case-management priority list |
| Q24 | Member age distribution | Population profile | Counts per 10-year band | Age mix drives risk & utilization |
| Q25 | Average claims per member | Utilization baseline | Single average | Population trending baseline |

## Provider Analytics — `sql/providers/provider_analytics.sql` (Q26–Q30)

| # | Query | Business purpose | Expected result | Healthcare interpretation |
|---|-------|------------------|-----------------|---------------------------|
| Q26 | Providers by specialty | Supply mix | Count per specialty | Network composition |
| Q27 | Network vs out-of-network | Network status split | Count per network_status | Out-of-network drives member cost |
| Q28 | Active providers | Current roster | Count where is_current | The live provider network size |
| Q29 | Provider historical versions | SCD2 change tracking | Versions per provider | Demonstrates dimension history |
| Q30 | Top specialties by claim volume | Demand by specialty | Ranked specialties | Aligns supply to demand |

## Data Quality Analytics — `sql/data_quality/data_quality_analytics.sql` (Q31–Q35)

| # | Query | Business purpose | Expected result | Healthcare interpretation |
|---|-------|------------------|-----------------|---------------------------|
| Q31 | Quarantined claims summary | Rejections by reason | Count per rejection_reason | Front-line data-quality signal |
| Q32 | Quarantine volume by dataset | Rejections by source | Count per dataset | Which source needs remediation |
| Q33 | Late-arriving claims | Timeliness | Late count, %, avg/max days | Feeds IBNR reserving |
| Q34 | Duplicate NPIs | Identity integrity | NPIs used by >1 provider | Identity-resolution defects |
| Q35 | Missing specialties | Completeness | Count/% missing specialty | Reduces provider-analytics reliability |

---

## Interview talking points

- **Layered warehouse.** The queries sit on top of a Bronze → Silver → Gold
  medallion architecture; the analytics layer only touches Gold marts plus the
  Silver quarantine, keeping business logic in dbt.
- **Only real schema.** Every column referenced exists in the dbt models; an
  automated test (`tests/sql/test_analytics_sql.py`) guards against fabricated
  tables and can execute each query against the built warehouse.
- **Healthcare fluency.** Denial rate, IBNR / late-arriving claims, network
  adequacy, SCD2 provider history, and NPI integrity are all payer-domain
  concepts a healthcare data engineer is expected to know.
- **Data quality as a first-class concern.** Quarantine and completeness
  metrics show the pipeline surfaces bad data instead of silently dropping it.
- **Portable SQL.** DuckDB SQL here maps cleanly to Athena/Presto for a cloud
  lakehouse, which is the Stage 5 direction.
