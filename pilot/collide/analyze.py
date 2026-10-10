"""Per-library collision statistics for the sampled libraries, observed and under a size-matched null.

Observed: for each sampled library, hard collisions (duplicate normalised name / description / content hash) and the
          cosine similarity between every pair of DISTINCT descriptions (embeddings in out/emb.npy).
Null    : the same statistics for n skills drawn at random, without replacement, from sampled skills of OTHER
          repositories (one draw per library, numpy seed 20261008). Controls for size and chance, not for topic.
Outputs : out/lib_stats.parquet  one row per library, columns for observed (o_*) and null (z_*)
          out/skill_nn.parquet   one row per skill occurrence: similarity to its nearest neighbour in the library
          out/pairs_band.parquet up to KEEP uniformly sampled within-library pairs per 0.05 band from 0.70 to 1.00
          out/pairs_libmax.parquet the most similar pair of each library
"""
import duckdb, numpy as np, pandas as pd

SEED, KEEP = 20261008, 400
TAUS = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
BANDS = [(round(0.70 + 0.05 * k, 2), round(0.75 + 0.05 * k, 2)) for k in range(6)]

con = duckdb.connect('collide.duckdb', read_only=True)
sk = con.execute("SELECT lib_id, repo, file_sha, name_norm, desc_id FROM sskill ORDER BY lib_id").fetchdf()
E = np.load('out/emb.npy', mmap_mode='r'); E = np.asarray(E)
rng = np.random.default_rng(SEED)

name_code = pd.factorize(sk.name_norm)[0]; sha_code = pd.factorize(sk.file_sha)[0]; repo_code = pd.factorize(sk.repo)[0]
desc = sk.desc_id.to_numpy(); lib = sk.lib_id.to_numpy()
starts = np.flatnonzero(np.r_[True, lib[1:] != lib[:-1]]); ends = np.r_[starts[1:], len(lib)]


def stats(rows, want_pairs=False):
    """Collision statistics for one set of skill rows (indices into sk)."""
    n = len(rows); d = desc[rows]
    out = {'n': n, 'dup_name': len(np.unique(name_code[rows])) < n, 'dup_desc': len(np.unique(d)) < n,
           'dup_sha': len(np.unique(sha_code[rows])) < n}
    u, inv, cnt = np.unique(d, return_inverse=True, return_counts=True)
    out['n_desc'] = len(u)
    if len(u) >= 2:
        S = E[u] @ E[u].T
        np.fill_diagonal(S, -1.0)
        nn_u = S.max(1); out['max_sim'] = float(nn_u.max())
    else:
        S = None; nn_u = np.full(len(u), -1.0); out['max_sim'] = -1.0
    nn = np.where(cnt[inv] > 1, 1.0, nn_u[inv])              # a skill sharing its description has a neighbour at 1.0
    for t in TAUS:
        out[f'k_soft_{int(t*100)}'] = int((nn_u[inv] >= t).sum())      # skills with a distinct-description neighbour >= t
        out[f'k_any_{int(t*100)}'] = int((nn >= t).sum())              # ... or an identical-description neighbour
    pairs = None
    if want_pairs and S is not None:
        i, j = np.nonzero(np.triu(S >= 0.70, 1))
        pairs = (u[i], u[j], S[i, j])
        a = int(np.argmax(S)); out['max_i'], out['max_j'] = int(u[a // len(u)]), int(u[a % len(u)])
    return out, nn, pairs


obs, nul, nn_all = [], [], np.empty(len(sk), dtype=np.float32)
res = {b: [] for b in BANDS}                                   # reservoir per band: (key, lib_id, di, dj, sim)
all_rows = np.arange(len(sk))
for a, b in zip(starts, ends):
    rows = all_rows[a:b]; lid = int(lib[a])
    o, nn, pairs = stats(rows, want_pairs=True)
    nn_all[a:b] = nn; o['lib_id'] = lid; obs.append(o)
    if pairs is not None and len(pairs[2]):
        di, dj, s = pairs; keys = rng.random(len(s))
        for lo, hi in BANDS:
            m = np.flatnonzero((s >= lo) & (s < hi if hi < 1.0 else s <= 1.0001))
            if len(m) > KEEP:                                   # the KEEP smallest keys of this library are enough:
                m = m[np.argpartition(keys[m], KEEP)[:KEEP]]    # the global sample keeps the KEEP smallest keys overall
            if len(m):
                res[(lo, hi)] += list(zip(keys[m].tolist(), [lid] * len(m), di[m].tolist(), dj[m].tolist(), s[m].tolist()))
                if len(res[(lo, hi)]) > 4 * KEEP:
                    res[(lo, hi)] = sorted(res[(lo, hi)])[:KEEP]
    # size-matched null: n random skills from other repositories
    n = b - a; pick = np.empty(0, dtype=np.int64)
    while len(pick) < n:
        cand = rng.choice(len(sk), size=min(len(sk), n - len(pick) + 16), replace=False)
        cand = cand[repo_code[cand] != repo_code[a]]
        cand = cand[~np.isin(cand, pick)]                       # keep draw order; never re-use a row
        pick = np.r_[pick, cand][:n]
    z, _, _ = stats(pick); z['lib_id'] = lid; nul.append(z)

O = pd.DataFrame(obs).set_index('lib_id'); Z = pd.DataFrame(nul).set_index('lib_id')
out = O.add_prefix('o_').join(Z.add_prefix('z_')).reset_index()
out.to_parquet('out/lib_stats.parquet')
pd.DataFrame({'lib_id': lib, 'desc_id': desc, 'nn_sim': nn_all}).to_parquet('out/skill_nn.parquet')
rows = [(lo, hi, lid, int(di), int(dj), float(s)) for (lo, hi), v in res.items() for _, lid, di, dj, s in sorted(v)[:KEEP]]
pd.DataFrame(rows, columns=['lo', 'hi', 'lib_id', 'desc_i', 'desc_j', 'sim']).to_parquet('out/pairs_band.parquet')
O.reset_index()[['lib_id', 'n', 'max_sim', 'max_i', 'max_j']].dropna().to_parquet('out/pairs_libmax.parquet')
print('libraries', len(out), '| skills', len(sk), '| pairs kept per band', {k: min(len(v), KEEP) for k, v in res.items()})
