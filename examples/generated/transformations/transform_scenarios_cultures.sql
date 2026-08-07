-- Generated transformation for scenarios_cultures
-- Source: 2 upstream dataset(s)
-- Generated at: 2026-08-06T22:22:24.895014

with source_data as (
    select
        *
    from {{ ref('upstream_table') }}
    where 1=1
    -- Add incremental logic here
    {% if is_incremental() %}
        and updated_at > (select max(updated_at) from {{ this }})
    {% endif %}
)

select * from source_data
