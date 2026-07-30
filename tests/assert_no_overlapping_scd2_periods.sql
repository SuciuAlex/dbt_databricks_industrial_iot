-- Singular test: fails if any two silver_dim_machines SCD2 periods for the
-- same machine overlap, i.e. one row's valid_from falls inside another
-- row's [valid_from, valid_to) window.

select
    a.machine_id,
    a.machine_sk  as machine_sk_a,
    b.machine_sk  as machine_sk_b,
    a.valid_from  as a_valid_from,
    a.valid_to    as a_valid_to,
    b.valid_from  as b_valid_from,
    b.valid_to    as b_valid_to
from {{ ref('silver_dim_machines') }} a
inner join {{ ref('silver_dim_machines') }} b
    on a.machine_id = b.machine_id
   and a.machine_sk != b.machine_sk
where b.valid_from >= a.valid_from
  and b.valid_from < coalesce(a.valid_to, cast('9999-12-31' as timestamp))
