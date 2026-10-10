"""Born-stale check on the rebuilt history: was the skill first committed after a model it names had been retired?

Inputs : hist/*.parquet (representative copies with commit history), flagged_occurrences.csv (first_ret per skill).
Cut-off: a skill counts only if the model was retired on or before CUTOFF (default 2026-07-08, before collection).
Usage  : python born_stale.py [CUTOFF]
"""
import sys, duckdb
CUT = sys.argv[1] if len(sys.argv) > 1 else '2026-07-08'
con = duckdb.connect()
con.execute(f"""CREATE TABLE b AS
  WITH h AS (SELECT file_sha, any_value(repo) AS repo, any_value(first_commit_at) AS first_at, max(commit_count) AS commits,
                    bool_or(first_ai_coauthor) AS first_ai FROM read_parquet('hist/*.parquet') GROUP BY 1),
       f AS (SELECT file_sha, min(first_ret) AS first_ret FROM read_csv_auto('flagged_occurrences.csv') GROUP BY 1)
  SELECT h.*, f.first_ret, CAST(h.first_at AS DATE) > f.first_ret AS born_stale,
         date_diff('day', f.first_ret, CAST(h.first_at AS DATE)) AS lag_days
  FROM h JOIN f USING (file_sha) WHERE f.first_ret <= DATE '{CUT}' AND h.first_at >= '2025-10-01'""")
q = lambda s: con.execute(s).fetchall()
print('cut-off', CUT)
print('  dated flagged skills, repos:', q("SELECT count(*), count(DISTINCT repo) FROM b"))
print('  born stale % | median days late:', q("SELECT round(100*avg(born_stale::INT),1), median(lag_days) FILTER (WHERE born_stale) FROM b"))
print('  never-edited skills: n, born stale %:', q("SELECT count(*), round(100*avg(born_stale::INT),1) FROM b WHERE commits=1"))
print('  repos with >=1 born-stale skill %:', q("SELECT round(100*avg(m),1) FROM (SELECT repo, max(born_stale::INT) m FROM b GROUP BY 1)"))
print('  by AI co-author on first commit (flag, n, %):', q("SELECT first_ai, count(*), round(100*avg(born_stale::INT),1) FROM b GROUP BY 1 ORDER BY 1"))
print('  by retirement period (period, n, born stale %):', q("""SELECT CASE WHEN first_ret < DATE '2025-10-01' THEN '1 before Oct 2025'
        WHEN first_ret < DATE '2026-06-01' THEN '2 Oct 2025 - May 2026' ELSE '3 June 2026' END p, count(*), round(100*avg(born_stale::INT),1) FROM b GROUP BY 1 ORDER BY 1"""))
