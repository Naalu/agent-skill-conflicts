"""Independent re-derivation of Run 4 headline counts (separate code path from analyze.py)."""
import duckdb, numpy as np, pandas as pd, time
con = duckdb.connect('collide.duckdb', read_only=True)
E = np.load('out/emb.npy', mmap_mode='r')
sk = con.sql("select lib_id, name_norm, desc_id from sskill order by lib_id").df()
ls = pd.read_parquet('out/lib_stats.parquet').set_index('lib_id')
# 1. naive per-library recomputation, every library
t = time.time(); rec = {}
for lib, g in sk.groupby('lib_id'):
    ids = g.desc_id.to_numpy(); u = np.unique(ids)
    hard = (len(u) < len(ids)) or g.name_norm.duplicated().any()
    if len(u) >= 2:
        X = np.asarray(E[u], dtype=np.float64); S = X @ X.T; np.fill_diagonal(S, -2); m = S.max()
    else: m = np.nan
    rec[lib] = (len(ids), hard, m)
r = pd.DataFrame.from_dict(rec, orient='index', columns=['n', 'hard', 'm'])
print(f"recomputed {len(r)} libraries in {time.time() - t:.0f}s")
j = r.join(ls)
print("size matches:", (j.n == j.o_n).all(), " max |max_sim diff|:", np.nanmax(np.abs(j.m - j.o_max_sim)))
for tau in (70, 75, 80, 85, 90, 95):
    mine = (j.hard | (j.m >= tau / 100)).mean(); theirs = (j[f'o_k_any_{tau}'] > 0).mean()
    print(f"  tau 0.{tau}: recomputed {100 * mine:.2f}%  analyze.py {100 * theirs:.2f}%  null {100 * (j[f'z_k_any_{tau}'] > 0).mean():.2f}%")
print("hard (sample):", f"{100 * j.hard.mean():.2f}%")
# 2. hard collisions on the full eligible population, straight SQL on the base tables
print(con.sql("""
with e as (select repo, libdir from lib where n_skills >= 2),
s as (select o.repo, o.libdir, lower(trim(c.name)) nm,
             left(lower(trim(regexp_replace(c.description, '\\s+', ' ', 'g'))), 1024) ds
      from o join c using (file_sha) join e using (repo, libdir) where o.f_valid),
g as (select repo, libdir, count(*) n, count(distinct nm) dn, count(distinct ds) dd from s group by all)
select count(*) libs, round(100*avg((dn<n)::int),2) dup_name, round(100*avg((dd<n)::int),2) dup_desc,
       round(100*avg((dn<n or dd<n)::int),2) either from g""").df().to_string(index=False))
