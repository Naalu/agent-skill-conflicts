"""Build the valid-skill and library tables for the competing-skills pilot (DuckDB file collide.duckdb).

Tables
  c   : one row per distinct content (representative copy): fm (front matter valid), name, description
  o   : one row per SKILL.md occurrence: repo, path, folder, libdir, f_valid
  lib : one row per tool-visible library (repo x repository-root dot-directory/skills) with n_skills >= 1
Definitions are those of Run 1 (see RUNLOG.md).
"""
import duckdb
con = duckdb.connect('collide.duckdb')
con.execute("SET threads=2; SET memory_limit='5GB';")
con.execute("CREATE OR REPLACE VIEW a AS SELECT * FROM read_parquet('slim/*.parquet')")
con.execute("""CREATE OR REPLACE TABLE c AS
  SELECT file_sha, max(frontmatter_valid) AS fm, any_value(name) AS name, any_value(description) AS description
  FROM a WHERE dedup_primary=1 GROUP BY 1""")
con.execute(r"""CREATE OR REPLACE TABLE o AS
  SELECT a.repo_full_name AS repo, a.path, a.file_sha,
         regexp_extract(a.path, '([^/]+)/[^/]+$', 1) AS folder,
         CASE WHEN a.path LIKE '%/%/%' THEN regexp_replace(a.path, '/[^/]+/[^/]+$', '') WHEN a.path LIKE '%/%' THEN '' ELSE NULL END AS libdir,
         (a.filename='SKILL.md' AND c.fm=1 AND trim(coalesce(c.name,''))<>'' AND trim(coalesce(c.description,''))<>'') AS f_valid
  FROM a JOIN c USING (file_sha)""")
con.execute(r"""CREATE OR REPLACE TABLE lib AS
  SELECT repo, libdir, count(*) AS n_skills, count(DISTINCT file_sha) AS n_distinct
  FROM o WHERE f_valid AND regexp_matches(libdir, '^\.[A-Za-z0-9_\-]+/skills$') GROUP BY 1,2""")
q = lambda s: con.execute(s).fetchall()
print('occurrences, distinct contents, repos :', q("SELECT count(*), count(DISTINCT file_sha), count(DISTINCT repo_full_name) FROM a"))
print('valid occurrences, valid distinct      :', q("SELECT count(*), count(DISTINCT file_sha) FROM o WHERE f_valid"))
print('tool-visible libraries, skills, repos  :', q("SELECT count(*), sum(n_skills), count(DISTINCT repo) FROM lib"))
print('  share >=32, >=64, >=128              :', q("SELECT round(100*avg((n_skills>=32)::INT),2), round(100*avg((n_skills>=64)::INT),2), round(100*avg((n_skills>=128)::INT),2) FROM lib"))
print('eligible (>=2 skills): libraries, skills, repos, distinct contents:',
      q("""SELECT count(*), sum(n_skills), count(DISTINCT repo) FROM lib WHERE n_skills>=2"""),
      q(r"""SELECT count(DISTINCT o.file_sha) FROM o JOIN lib USING (repo, libdir) WHERE o.f_valid AND lib.n_skills>=2"""))
print('eligible size quantiles (p50,p75,p90,p99,max):', q("SELECT median(n_skills), quantile_cont(n_skills,0.75), quantile_cont(n_skills,0.9), quantile_cont(n_skills,0.99), max(n_skills) FROM lib WHERE n_skills>=2"))
print('libraries per repo among eligible (1,2,3+):', q("""SELECT sum((k=1)::INT), sum((k=2)::INT), sum((k>=3)::INT) FROM (SELECT repo, count(*) k FROM lib WHERE n_skills>=2 GROUP BY 1)"""))
