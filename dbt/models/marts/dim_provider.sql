-- dim_provider: provider dimension preserving version history (SCD Type 2).
-- The Silver providers table already carries valid_from / valid_to / is_current
-- version columns per (provider_id, effective_date). We expose a surrogate key
-- (no extra dbt packages required) so the fact table can join to the version
-- that was current at claim time.
with silver_providers as (
    select * from {{ source('silver', 'providers') }}
)

select
    md5(cast(provider_id as varchar) || '|' || cast(effective_date as varchar)) as provider_sk,
    provider_id,
    provider_name,
    specialty,
    npi,
    network_status,
    address_state,
    effective_date,
    valid_from,
    valid_to,
    is_current
from silver_providers
