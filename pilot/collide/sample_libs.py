"""Draw the library sample for the competing-skills pilot and list its skills and distinct descriptions.

Sample : N eligible libraries (tool-visible, >= 2 valid skills), chosen as the N smallest values of
         md5(repo | libdir | SEED). Deterministic; equivalent to a simple random sample.
Tables : slib  (lib_id, repo, libdir, n_skills)
         sskill(lib_id, repo, folder, file_sha, name_norm, desc_id)       one row per skill occurrence
         sdesc (desc_id, text)                                            one row per distinct normalised description
Normalisation: description -> whitespace collapsed, trimmed, lower-cased, cut at 1,024 characters (the spec cap).
               name        -> trimmed, lower-cased.
Usage  : python sample_libs.py N SEED
"""
import sys, duckdb
N, SEED = int(sys.argv[1]), sys.argv[2]
con = duckdb.connect('collide.duckdb')
con.execute("SET threads=2; SET memory_limit='5GB';")
con.execute(f"""CREATE OR REPLACE TABLE slib AS
  SELECT row_number() OVER (ORDER BY h) AS lib_id, repo, libdir, n_skills FROM (
    SELECT repo, libdir, n_skills, md5(repo || '|' || libdir || '|{SEED}') AS h FROM lib WHERE n_skills >= 2 ORDER BY h LIMIT {N})""")
con.execute(r"""CREATE OR REPLACE TABLE sraw AS
  SELECT s.lib_id, o.repo, o.folder, o.file_sha, lower(trim(c.name)) AS name_norm,
         left(lower(trim(regexp_replace(c.description, '\s+', ' ', 'g'))), 1024) AS desc_norm
  FROM slib s JOIN o USING (repo, libdir) JOIN c USING (file_sha) WHERE o.f_valid""")
con.execute("CREATE OR REPLACE TABLE sdesc AS SELECT row_number() OVER (ORDER BY desc_norm) - 1 AS desc_id, desc_norm AS text FROM (SELECT DISTINCT desc_norm FROM sraw)")
con.execute("CREATE OR REPLACE TABLE sskill AS SELECT r.lib_id, r.repo, r.folder, r.file_sha, r.name_norm, d.desc_id FROM sraw r JOIN sdesc d ON r.desc_norm = d.text")
con.execute("DROP TABLE sraw")
q = lambda s: con.execute(s).fetchall()
print('sampled libraries, repos, skills:', q("SELECT count(*), count(DISTINCT repo), sum(n_skills) FROM slib"), '| skill rows:', q("SELECT count(*) FROM sskill"))
print('distinct descriptions:', q("SELECT count(*), sum(length(text)), median(length(text)) FROM sdesc"))
print('sample size quantiles (p50,p90,p99,max):', q("SELECT median(n_skills), quantile_cont(n_skills,0.9), quantile_cont(n_skills,0.99), max(n_skills) FROM slib"))
