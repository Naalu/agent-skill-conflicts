"""Run 5 probes P1 (effective catalogues across directories) and P2 (listing size against product budgets).
Definitions are in RUNLOG.md, Run 5. Reads collide.duckdb (tables c, o, lib)."""
import duckdb, pandas as pd
pd.set_option('display.width', 220); pd.set_option('display.max_columns', 30)
con = duckdb.connect('collide.duckdb', read_only=True); con.execute("SET threads=2; SET memory_limit='5GB'")
q = lambda s: con.execute(s).fetchdf()
con.execute(r"""CREATE TEMP TABLE v AS
  SELECT o.repo, o.libdir, o.file_sha, lower(trim(c.name)) AS nm,
         left(lower(trim(regexp_replace(c.description, '\s+', ' ', 'g'))), 1024) AS ds,
         length(trim(c.name)) AS name_len, length(c.description) AS desc_len
  FROM o JOIN c USING (file_sha)
  WHERE o.f_valid AND regexp_matches(o.libdir, '^\.[A-Za-z0-9_\-]+/skills$')""")
print('valid tool-visible skills:', q("select count(*) n, count(distinct repo) repos, count(distinct repo||'|'||libdir) libs from v").to_string(index=False))
print('repositories by number of skill directories:', q("select k, count(*) repos from (select repo, count(distinct libdir) k from v group by 1) group by 1 order by 1 limit 8").to_string(index=False))

PRODUCTS = {'Claude Code': ['.claude'], 'Codex': ['.agents'], 'Copilot / VS Code': ['.github', '.claude', '.agents'],
            'Cursor': ['.cursor', '.agents', '.claude', '.codex'], 'OpenCode': ['.opencode', '.claude', '.agents'],
            'Gemini CLI': ['.gemini', '.agents']}
rows = []; rows2 = []
for p, dirs in PRODUCTS.items():
    inl = ",".join(f"'{d}/skills'" for d in dirs)
    con.execute(f"CREATE OR REPLACE TEMP TABLE pv AS SELECT * FROM v WHERE libdir IN ({inl})")
    # P1: cross-directory same-name skills
    r = q("""
      WITH rd AS (SELECT repo, count(DISTINCT libdir) k FROM pv GROUP BY 1),
           nm AS (SELECT repo, nm, count(DISTINCT libdir) kd, count(DISTINCT file_sha) ks, count(DISTINCT ds) kdesc FROM pv GROUP BY 1,2),
           rr AS (SELECT repo, max((kd>=2)::INT) same_name, max((kd>=2 AND ks>=2)::INT) diverged, max((kd>=2 AND kdesc>=2)::INT) diff_desc,
                         sum((kd>=2)::INT) n_names, sum((kd>=2 AND ks>=2)::INT) n_div FROM nm GROUP BY 1)
      SELECT count(*) repos_any, sum((k>=2)::INT) repos_multi,
             sum(same_name) FILTER (WHERE k>=2) repos_same_name, sum(diverged) FILTER (WHERE k>=2) repos_diverged,
             sum(diff_desc) FILTER (WHERE k>=2) repos_diff_desc, sum(n_names) names_mirrored, sum(n_div) names_diverged
      FROM rd JOIN rr USING (repo)""").iloc[0].to_dict()
    r['product'] = p; rows.append(r)
    # P2: listing size of the product's catalogue (union of its directories in one repository)
    for cap in (1536, 1024):
        s = q(f"""WITH cat AS (SELECT repo, count(*) n, sum(name_len + least(desc_len, {cap})) chars FROM pv GROUP BY 1)
                 SELECT count(*) cats, median(chars) med, quantile_cont(chars, 0.9) p90,
                        round(100*avg((chars>5440)::INT),2) over_5440, round(100*avg((chars>8000)::INT),2) over_8000,
                        round(100*avg((chars>16000)::INT),2) over_16000, round(100*avg((chars>40000)::INT),2) over_40000,
                        round(100*avg((chars>8000)::INT) FILTER (WHERE n>=2),2) over_8000_n2, sum((n>=2)::INT) cats_n2 FROM cat""").iloc[0].to_dict()
        s['product'] = p; s['cap'] = cap; rows2.append(s)
d = pd.DataFrame(rows).set_index('product')
d['pct_multi'] = (100 * d.repos_multi / d.repos_any).round(1)
d['pct_same_name_of_multi'] = (100 * d.repos_same_name / d.repos_multi).round(1)
d['pct_diverged_of_same'] = (100 * d.repos_diverged / d.repos_same_name).round(1)
d['pct_diffdesc_of_same'] = (100 * d.repos_diff_desc / d.repos_same_name).round(1)
d['pct_diverged_of_any'] = (100 * d.repos_diverged / d.repos_any).round(2)
print('\nP1 cross-directory same-name skills, by product'); print(d.to_string())
print('\nP2 listing size (characters), catalogue = union of the product directories in one repository'); print(pd.DataFrame(rows2).set_index(['product', 'cap']).to_string())
# single-directory view, all tool-visible libraries (the Run 4 unit)
print('\nP2 single directory, all libraries / eligible (>=2 skills), cap 1536')
print(q("""WITH cat AS (SELECT repo, libdir, count(*) n, sum(name_len + least(desc_len, 1536)) chars FROM v GROUP BY 1,2)
          SELECT count(*) libs, round(100*avg((chars>5440)::INT),2) over_5440, round(100*avg((chars>8000)::INT),2) over_8000, round(100*avg((chars>16000)::INT),2) over_16000,
                 round(100*avg((chars>40000)::INT),2) over_40000, sum((n>=2)::INT) eligible,
                 round(100*avg((chars>8000)::INT) FILTER (WHERE n>=2),2) elig_over_8000, round(100*avg((chars>5440)::INT) FILTER (WHERE n>=2),2) elig_over_5440,
                 median(n) FILTER (WHERE chars>8000) med_skills_over_8000 FROM cat""").to_string(index=False))
