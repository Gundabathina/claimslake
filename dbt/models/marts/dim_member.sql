-- dim_member: one row per member (member dimension).
-- Sourced directly from the Silver members table, which is already
-- deduplicated to one row per member_id by the PySpark layer.
with silver_members as (
    select * from {{ source('silver', 'members') }}
)

select
    member_id,
    plan_type,
    state,
    zip_code,
    gender,
    date_of_birth,
    has_missing_zip,
    source_system
from silver_members
