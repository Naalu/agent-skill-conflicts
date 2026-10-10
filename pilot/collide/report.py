"""Summarise out/lib_stats.parquet: collision rates by threshold, against the null, and by strata."""
import duckdb, pandas as pd
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
con = duckdb.connect('collide.duckdb', read_only=True)
con.execute("CREATE TEMP VIEW s AS SELECT * FROM read_parquet('out/lib_stats.parquet')")
con.execute("CREATE TEMP VIEW r AS SELECT full_name AS repo, stars, is_fork, language, created_at, pushed_at FROM read_parquet('repos.parquet')")
TAUS = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
q = lambda x: con.execute(x).fetchdf()

print('libraries:', q("SELECT count(*) n, sum(o_n) skills, round(100*avg((o_dup_name)::INT),2) dup_name, round(100*avg(o_dup_desc::INT),2) dup_desc, round(100*avg((o_dup_name OR o_dup_desc)::INT),2) any_hard, round(100*avg((z_dup_name OR z_dup_desc)::INT),2) null_any_hard FROM s").to_string(index=False))
rows = []
for t in TAUS:
    c = f"(o_max_sim >= {t} OR o_dup_name OR o_dup_desc)"; z = f"(z_max_sim >= {t} OR z_dup_name OR z_dup_desc)"
    k = int(t * 100)
    rows.append(q(f"""SELECT {t} AS tau,
        round(100*avg((o_max_sim >= {t})::INT),2) AS soft_only, round(100*avg({c}::INT),2) AS k1_any,
        round(100*avg({z}::INT),2) AS null_any, round(avg({c}::INT)/nullif(avg({z}::INT),0),1) AS ratio,
        round(100*avg({c}::INT) FILTER (WHERE o_n BETWEEN 2 AND 20),2) AS k3_size_2_20,
        round(100*avg({z}::INT) FILTER (WHERE o_n BETWEEN 2 AND 20),2) AS null_2_20,
        round(100.0*sum(o_k_any_{k})/sum(o_n),2) AS pct_skills_with_neighbour,
        round(100.0*sum(z_k_any_{k})/sum(z_n),2) AS null_pct_skills
      FROM s"""))
print(pd.concat(rows).to_string(index=False))
for t in (0.80, 0.90):
    c = f"(o_max_sim >= {t} OR o_dup_name OR o_dup_desc)"; z = f"(z_max_sim >= {t} OR z_dup_name OR z_dup_desc)"
    print(f'\nby library size, tau={t}')
    print(q(f"""SELECT CASE WHEN o_n=2 THEN '02' WHEN o_n<=5 THEN '03-05' WHEN o_n<=10 THEN '06-10' WHEN o_n<=20 THEN '11-20'
                 WHEN o_n<=50 THEN '21-50' ELSE '51+' END AS size, count(*) libs, round(100*avg({c}::INT),1) observed, round(100*avg({z}::INT),1) null_rate
               FROM s GROUP BY 1 ORDER BY 1""").to_string(index=False))
    print(f'by stars and fork status, tau={t}')
    print(q(f"""SELECT CASE WHEN r.stars IS NULL THEN 'unknown' WHEN r.stars=0 THEN '0' WHEN r.stars<10 THEN '1-9' WHEN r.stars<100 THEN '10-99' ELSE '100+' END AS stars,
                 count(*) libs, round(100*avg({c}::INT),1) observed, round(100*avg({z}::INT),1) null_rate, median(o_n) med_size
               FROM s JOIN slib USING (lib_id) LEFT JOIN r USING (repo) GROUP BY 1 ORDER BY 1""").to_string(index=False))
    print(q(f"""SELECT r.is_fork, count(*) libs, round(100*avg({c}::INT),1) observed FROM s JOIN slib USING (lib_id) LEFT JOIN r USING (repo) GROUP BY 1 ORDER BY 1""").to_string(index=False))
print('\none library per repository (largest), tau grid:')
print(q("""WITH x AS (SELECT s.*, row_number() OVER (PARTITION BY slib.repo ORDER BY o_n DESC, lib_id) rk FROM s JOIN slib USING (lib_id))
           SELECT count(*) repos, """ + ", ".join(f"round(100*avg((o_max_sim >= {t} OR o_dup_name OR o_dup_desc)::INT),2) AS t{int(t*100)}" for t in TAUS) + " FROM x WHERE rk=1").to_string(index=False))
