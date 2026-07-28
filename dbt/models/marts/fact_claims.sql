-- fact_claims: one row per claim, the central fact of the star schema.
-- Grain: claim_id. Joins to dim_member and (the current version of)
-- dim_provider, and derives simple financial + quality measures used by the
-- analytics queries in sql/.
with claims as (
    select * from {{ source('silver', 'claims') }}
),

members as (
    select member_id, plan_type, state from {{ ref('dim_member') }}
),

providers_current as (
    select provider_id, provider_sk, specialty, network_status
    from {{ ref('dim_provider') }}
    where is_current = true
)

select
    c.claim_id,
    c.member_id,
    c.provider_id,
    p.provider_sk,
    c.diagnosis_code,
    c.service_date,
    c.service_year_month,
    c.claim_status,
    c.denial_reason,
    m.plan_type,
    m.state              as member_state,
    p.specialty          as provider_specialty,
    p.network_status,
    cast(c.billed_amount as double) as billed_amount,
    cast(c.paid_amount as double)   as paid_amount,
    cast(c.billed_amount as double) - cast(c.paid_amount as double) as unpaid_amount,
    case when lower(c.claim_status) = 'denied' then 1 else 0 end as is_denied,
    c.is_late_arriving,
    c.days_late
from claims c
left join members m on c.member_id = m.member_id
left join providers_current p on c.provider_id = p.provider_id
