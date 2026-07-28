-- Singular test: fails if any machine_id in silver_dim_machines has zero or
-- more than one is_current = true row. Exactly one current row per machine
-- is a core invariant of the SCD2 design.

select
    machine_id,
    count(*) as current_row_count
from {{ ref('silver_dim_machines') }}
where is_current = true
group by machine_id
having count(*) != 1
