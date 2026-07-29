-- dim_provider: provider dimension with SCD Type 2 version history.
--
-- The Silver providers table intentionally preserves one row per
-- (provider_id, effective_date) version (see build_silver_providers): rows that
-- share provider_id but differ in network_status / effective_date are kept as
-- distinct historical versions. Silver does NOT carry valid_from / valid_to /
-- is_current -- those are DERIVED here in the Gold layer from the real
-- effective_date column, which is the honest source of version ordering.
--
-- valid_from = this version's effective_date
-- valid_to   = the next version's effective_date (NULL for the latest version)
-- is_current = TRUE when there is no later version
-- provider_sk = stable surrogate key from real columns (provider_id, effective_date)
with silver_providers as (
    select * from {{ source('silver', 'providers') }}
),

versioned as (
    select
        provider_id,
        provider_name,
        specialty,
        npi,
        network_status,
        address_state,
        effective_date,
        lead(effective_date) over (
            partition by provider_id
            order by effective_date
        ) as next_effective_date
    from silver_providers
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
    effective_date            as valid_from,
    next_effective_date       as valid_to,
    (next_effective_date is null) as is_current
from versioned
