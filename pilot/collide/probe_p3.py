"""Run 5 probe P3: invocation-related front-matter fields (fm/*.parquet from fm_scan.py)."""
import duckdb, pandas as pd
pd.set_option('display.width', 220)
con = duckdb.connect('collide.duckdb', read_only=True); con.execute("SET threads=2; SET memory_limit='5GB'")
q = lambda s: con.execute(s).fetchdf()
con.execute("CREATE TEMP TABLE f AS SELECT file_sha, bool_or(dmi) dmi, bool_or(not_user_invocable) nui, bool_or(has_paths) paths, bool_or(has_wtu) wtu, max(fm_chars) fm_chars FROM read_parquet('fm/*.parquet') GROUP BY 1")
print('representative copies scanned:', q("select count(*) n, sum((fm_chars>0)::int) with_front_matter from f").to_string(index=False))
con.execute(r"""CREATE TEMP TABLE v AS SELECT o.repo, o.libdir, o.file_sha, coalesce(f.dmi,false) dmi, coalesce(f.nui,false) nui, coalesce(f.paths,false) paths, coalesce(f.wtu,false) wtu, (f.file_sha IS NULL) missing
  FROM o LEFT JOIN f USING (file_sha) WHERE o.f_valid AND regexp_matches(o.libdir, '^\.[A-Za-z0-9_\-]+/skills$')""")
print('valid tool-visible skills, all directories'); print(q("""select count(*) skills, round(100*avg(missing::int),2) pct_not_scanned, round(100*avg(dmi::int),2) pct_dmi, round(100*avg(nui::int),2) pct_not_user_invocable,
  round(100*avg(paths::int),2) pct_paths, round(100*avg(wtu::int),2) pct_when_to_use from v""").to_string(index=False))
print('by directory'); print(q("""select libdir, count(*) skills, round(100*avg(dmi::int),2) pct_dmi, round(100*avg(paths::int),2) pct_paths, round(100*avg(wtu::int),2) pct_wtu
  from v group by 1 having count(*)>20000 order by 2 desc""").to_string(index=False))
print('eligible libraries (>=2 skills)'); print(q("""with l as (select repo, libdir, count(*) n, sum(dmi::int) k, sum((not dmi)::int) invocable from v group by 1,2 having count(*)>=2)
  select count(*) libs, round(100*avg((k>0)::int),2) pct_libs_with_dmi, round(100*avg((invocable<2)::int),2) pct_libs_under_2_invocable, round(100.0*sum(k)/sum(n),2) pct_skills_dmi from l""").to_string(index=False))
# Run 4 most-similar pairs: is either member closed to model invocation?
lm = pd.read_parquet('out/pairs_libmax.parquet'); con.register('lm', lm)
print('Run 4 most-similar pairs'); print(q("""with m as (select s.lib_id, s.desc_id, bool_and(coalesce(f.dmi,false)) dmi_all from sskill s left join f using (file_sha) group by 1,2),
  p as (select lm.lib_id, lm.max_sim, (a.dmi_all or b.dmi_all) any_dmi from lm join m a on a.lib_id=lm.lib_id and a.desc_id=lm.max_i join m b on b.lib_id=lm.lib_id and b.desc_id=lm.max_j)
  select count(*) pairs, round(100*avg(any_dmi::int),2) pct_pair_has_dmi, round(100*avg(any_dmi::int) filter (where max_sim>=0.7),2) pct_ge_070 from p""").to_string(index=False))
