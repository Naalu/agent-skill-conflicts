"""Build the working dataset: population ladder P0-P3, skill-level exclusions, bulk and boilerplate flags.

Implements the run-log entry "Working dataset v1" (2026-11-03). Read that entry first; nothing here changes a rule.

Inputs (defaults assume src/body_scan.py has run; override with flags)
  --slim   folder of slimmed artifacts parts (data/interim/slim, written by src/body_scan.py)
  --repos  repos.parquet (data/interim/repos.parquet, written by src/body_scan.py)
  --body   optional: data/interim/body_flags.parquet from src/body_scan.py (one row per file_sha). Without it the
           body-based skill exclusions (instruction lines, token floor, placeholder text) and the skeleton-based bulk
           flag are NOT applied, and the cascade says so.

Outputs (data/interim/)
  working_set.parquet   one row per P0 repository: counts, flags, rung membership, cluster id, representative flag
  skills.parquet        one row per valid root-directory skill occurrence with its exclusion flags (RQ inputs)
  cascade.csv           repositories and skills remaining after each step, with the rule that removed them
  thresholds.json       the fence, the boilerplate N and the cluster count as computed, for the run log

Usage
  uv run python src/build_working_set.py [--slim DIR] [--repos FILE] [--body FILE] [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict

import duckdb
import numpy as np
import pandas as pd

SEED = 20261008
GAO_KEYWORDS = ["awesome", "collection", "tutorial", "course", "registry"]
EXT_KEYWORDS = ["marketplace", "plugins", "catalog", "catalogue", "library", "hub"]
ROOT_SKILL_PATH = r"^\.[A-Za-z0-9_\-]+/skills/[^/]+/SKILL\.md$"
JACCARD = 0.8
MIN_SHARED = 5
MINHASH_PERMS = 64
BANDS = 16  # 16 bands x 4 rows: catches Jaccard 0.8 pairs with probability ~0.995


def tokens(s) -> set[str]:
    if not isinstance(s, str):  # None or NaN from a missing description
        return set()
    return set(re.split(r"[^a-z0-9]+", s.lower())) - {""}


def keyword_flags(name: str, desc: str) -> tuple[bool, bool, bool]:
    """(gao, extension, skills-affix) on the repository name (after the owner) and description."""
    short = name.split("/", 1)[1] if "/" in name else name
    t = tokens(short) | tokens(desc)
    gao = any(k in t for k in GAO_KEYWORDS)
    ext = any(k in t for k in EXT_KEYWORDS)
    affix = bool(re.search(r"(^|[-_.])skills?([-_.]|$)", short.lower())) and "skills" in tokens(short)
    return gao, ext, affix


def pick(cols: list[str], *candidates: str) -> str | None:
    for c in candidates:
        if c in cols:
            return c
    return None


def minhash_clusters(sets: dict[str, list[str]]) -> dict[str, int]:
    """Union-find over repositories whose skill-hash sets have Jaccard >= JACCARD with >= MIN_SHARED shared hashes,
    or identical sets. Candidate pairs come from MinHash LSH; every candidate is checked exactly."""
    rng = np.random.default_rng(SEED)
    universe = {h for s in sets.values() for h in s}
    hid = {h: i for i, h in enumerate(sorted(universe))}
    a = rng.integers(1, 2**31 - 1, MINHASH_PERMS, dtype=np.int64)
    b = rng.integers(0, 2**31 - 1, MINHASH_PERMS, dtype=np.int64)
    prime = 2**31 - 1
    repos = list(sets)
    parent = {r: r for r in repos}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    # identical fingerprints: exact, no hashing needed
    by_fp: dict[tuple, str] = {}
    for r in repos:
        fp = tuple(sorted(sets[r]))
        if fp in by_fp:
            union(by_fp[fp], r)
        else:
            by_fp[fp] = r
    # LSH only over repositories with enough skills to meet MIN_SHARED
    big = [r for r in repos if len(sets[r]) >= MIN_SHARED]
    sigs = {}
    for r in big:
        ids = np.array([hid[h] for h in sets[r]], dtype=np.int64)
        sigs[r] = ((np.outer(a, ids) + b[:, None]) % prime).min(axis=1)
    rows = MINHASH_PERMS // BANDS
    cand = set()
    for band in range(BANDS):
        buckets = defaultdict(list)
        for r in big:
            buckets[tuple(sigs[r][band * rows:(band + 1) * rows])].append(r)
        for members in buckets.values():
            if 1 < len(members) <= 2000:  # a bucket this size is a template family; exact check below still applies
                for i in range(len(members)):
                    for j in range(i + 1, len(members)):
                        cand.add((members[i], members[j]))
    checked = 0
    for x, y in cand:
        sx, sy = set(sets[x]), set(sets[y])
        inter = len(sx & sy)
        if inter >= MIN_SHARED and inter / len(sx | sy) >= JACCARD:
            union(x, y)
            checked += 1
    roots = {r: find(r) for r in repos}
    ids = {root: i for i, root in enumerate(sorted(set(roots.values())))}
    print(f"clusters: {len(cand)} LSH candidates, {checked} confirmed pairs, {len(ids)} clusters over {len(repos)} repos")
    return {r: ids[roots[r]] for r in repos}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slim", default="data/interim/slim")
    ap.add_argument("--repos", default="data/interim/repos.parquet")
    ap.add_argument("--body", default="data/interim/body_flags.parquet")
    ap.add_argument("--out", default="data/interim")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    have_body = os.path.exists(args.body)
    if not have_body:
        print("NOTE: no body flags file; body-based exclusions and the skeleton bulk flag are not applied", file=sys.stderr)

    con = duckdb.connect()
    con.execute("SET threads=4; SET memory_limit='6GB'; SET preserve_insertion_order=false;")
    con.execute(f"CREATE VIEW a AS SELECT * FROM read_parquet('{args.slim}/*.parquet')")
    con.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{args.repos}')")
    rcols = [c[0] for c in con.execute("DESCRIBE r").fetchall()]
    c_name = pick(rcols, "full_name", "repo_full_name")
    c_fork = pick(rcols, "fork", "is_fork")
    c_lang = pick(rcols, "language", "primary_language")
    c_stars = pick(rcols, "stars", "stargazers_count", "stargazers")
    c_desc = pick(rcols, "description")
    c_owner = pick(rcols, "owner", "owner_login")
    missing = [n for n, c in [("full_name", c_name), ("fork", c_fork), ("language", c_lang), ("stars", c_stars)] if c is None]
    if missing:
        sys.exit(f"repos.parquet lacks columns for {missing}; columns are {rcols}")
    desc_expr = f"r.{c_desc}" if c_desc else "''"
    owner_expr = f"r.{c_owner}" if c_owner else f"split_part(r.{c_name}, '/', 1)"

    # representative content per hash, then valid root-directory skill occurrences
    con.execute("""CREATE TABLE c AS
        SELECT file_sha, max(frontmatter_valid) AS fm, any_value(name) AS name, any_value(description) AS description,
               any_value(body_chars) AS body_chars, min(first_commit_at) AS first_commit_at
        FROM a WHERE dedup_primary = 1 GROUP BY 1""")
    con.execute(rf"""CREATE TABLE o AS
        SELECT a.repo_full_name AS repo, a.path, a.file_sha, a.location_class,
               regexp_replace(a.path, '/[^/]+/[^/]+$', '') AS libdir,
               (a.filename = 'SKILL.md' AND c.fm = 1 AND trim(coalesce(c.name, '')) <> ''
                AND trim(coalesce(c.description, '')) <> '') AS f_valid
        FROM a JOIN c USING (file_sha)
        WHERE regexp_matches(a.path, '{ROOT_SKILL_PATH}')""")
    if have_body:
        con.execute(f"CREATE VIEW bf AS SELECT * FROM read_parquet('{args.body}')")
        con.execute("""CREATE TABLE s AS
            SELECT o.*, c.name, c.description, c.first_commit_at,
                   coalesce(bf.instruction_lines < 10, false) AS x_short,
                   coalesce(bf.meaningful_tokens < 5, false) AS x_tokens,
                   coalesce(bf.placeholder, false) AS x_placeholder,
                   coalesce(bf.dmi, false) AS dmi, bf.skeleton
            FROM o JOIN c USING (file_sha) LEFT JOIN bf USING (file_sha) WHERE o.f_valid""")
    else:
        con.execute("""CREATE TABLE s AS
            SELECT o.*, c.name, c.description, c.first_commit_at,
                   false AS x_short, false AS x_tokens, false AS x_placeholder, NULL::BOOLEAN AS dmi, NULL::VARCHAR AS skeleton
            FROM o JOIN c USING (file_sha) WHERE o.f_valid""")
    con.execute("ALTER TABLE s ADD COLUMN excluded BOOLEAN")
    con.execute("UPDATE s SET excluded = x_short OR x_tokens OR x_placeholder")

    # per-repository table over P0 (repositories with at least one valid root-directory skill)
    con.execute(f"""CREATE TABLE rep AS
        SELECT s.repo,
               count(*) AS n_skills_all,
               count(*) FILTER (WHERE NOT excluded) AS n_skills,
               count(DISTINCT lower(trim(name))) FILTER (WHERE NOT excluded) AS n_names,
               count(DISTINCT libdir) AS n_dirs,
               max((location_class = 'canonical')::INT) = 1 AS has_canonical,
               count(DISTINCT first_commit_at::DATE) FILTER (WHERE first_commit_at IS NOT NULL) AS n_dates,
               count(*) FILTER (WHERE first_commit_at IS NOT NULL) AS n_dated,
               max(cnt_date) AS max_same_date,
               count(*) FILTER (WHERE skeleton IS NOT NULL) AS n_skel,
               max(cnt_skel) AS max_same_skel,
               r.{c_fork} AS fork, r.{c_lang} AS language, r.{c_stars} AS stars, {desc_expr} AS description,
               {owner_expr} AS owner
        FROM (SELECT s.*,
                     CASE WHEN first_commit_at IS NULL THEN 0 ELSE count(*) OVER (PARTITION BY repo, first_commit_at::DATE) END AS cnt_date,
                     CASE WHEN skeleton IS NULL THEN 0 ELSE count(*) OVER (PARTITION BY repo, skeleton) END AS cnt_skel
              FROM s) s
        LEFT JOIN r ON r.{c_name} = s.repo
        GROUP BY s.repo, r.{c_fork}, r.{c_lang}, r.{c_stars}, {desc_expr}, {owner_expr}""")
    rep = con.execute("SELECT * FROM rep").fetchdf()
    print(f"P0: {len(rep):,} repositories, {int(rep.n_skills_all.sum()):,} valid skills, {int(rep.n_skills.sum()):,} after skill exclusions")

    kw = rep.apply(lambda x: keyword_flags(x.repo, x.description), axis=1, result_type="expand")
    rep["kw_gao"], rep["kw_ext"], rep["kw_affix"] = kw[0], kw[1], kw[2]
    rep["fork"] = pd.to_numeric(rep["fork"], errors="coerce").fillna(0).astype(int).astype(bool)  # 0/1 or bool
    rep["stars"] = pd.to_numeric(rep["stars"], errors="coerce")
    rep["p1"] = ~rep.fork
    # the fence and the language rule use distinct skill names, so a project that mirrors its skills into several
    # directories is not counted as if it had several times as many skills
    q1, q3 = rep.loc[rep.p1, "n_names"].quantile([0.25, 0.75])
    fence = float(q3 + 1.5 * (q3 - q1))
    rep["over_fence"] = rep.n_names > fence
    rep["lang_null_rule"] = rep.language.isna() & ~rep.has_canonical & (rep.n_names >= 2)
    rep["collection"] = rep.kw_gao | rep.kw_ext | rep.kw_affix | rep.over_fence | rep.lang_null_rule
    rep["collection_gao_only"] = rep.kw_gao | rep.over_fence
    rep["p2"] = rep.p1 & ~rep.collection
    rep["p2_gao_only"] = rep.p1 & ~rep.collection_gao_only

    # bulk/generated flag (sensitivity only)
    same_date_share = np.where(rep.n_dated > 0, rep.max_same_date / rep.n_dated.replace(0, np.nan), np.nan)
    skel_share = np.where(rep.n_skel > 0, rep.max_same_skel / rep.n_skel.replace(0, np.nan), np.nan)
    rep["bulk"] = rep.over_fence & ((same_date_share >= 0.9) | (skel_share >= 0.5))
    rep["bulk"] = rep["bulk"].fillna(False)

    # boilerplate content: distinct hashes spread over many owners
    spread = con.execute("""SELECT s.file_sha, count(DISTINCT rep.owner) AS owners
                            FROM s JOIN rep USING (repo) WHERE rep.fork = false GROUP BY 1""").fetchdf()
    n_boiler = int(np.ceil(spread.owners.quantile(0.999)))
    n_lo, n_hi = int(np.ceil(spread.owners.quantile(0.99))), int(np.ceil(spread.owners.quantile(0.9999)))
    boiler = set(spread.loc[spread.owners >= n_boiler, "file_sha"])
    con.execute("ALTER TABLE s ADD COLUMN boilerplate BOOLEAN")
    con.register("boiler_df", pd.DataFrame({"file_sha": sorted(boiler)}))
    con.execute("UPDATE s SET boilerplate = file_sha IN (SELECT file_sha FROM boiler_df)")

    # near-fork / template clusters over P2 (fingerprint = sorted set of valid, non-excluded skill hashes)
    fp_rows = con.execute("SELECT repo, list(DISTINCT file_sha) AS shas FROM s WHERE NOT excluded GROUP BY 1").fetchall()
    p2_set = set(rep.loc[rep.p2, "repo"])
    sets = {repo: shas for repo, shas in fp_rows if repo in p2_set}
    cl = minhash_clusters(sets)
    rep["cluster"] = rep.repo.map(cl)
    first = con.execute("SELECT repo, min(first_commit_at) AS fc FROM s GROUP BY 1").fetchdf().set_index("repo")["fc"]
    rep["first_commit"] = rep.repo.map(first)
    order = rep.loc[rep.p2].sort_values(["cluster", "first_commit", "stars", "repo"], ascending=[True, True, False, True],
                                        na_position="last")
    reps = set(order.drop_duplicates("cluster").repo)
    rep["p3"] = rep.p2 & rep.repo.isin(reps)
    rep["cluster_size"] = rep.cluster.map(rep.loc[rep.p2].cluster.value_counts())

    # cascade
    n_sk = lambda mask: int(rep.loc[mask, "n_skills"].sum())
    cascade = [
        ("P0 valid root-directory skill", len(rep), int(rep.n_skills_all.sum()), "ROOT_SKILL_PATH; valid front matter"),
        ("skill-level exclusions", int((rep.n_skills > 0).sum()), int(rep.n_skills.sum()), "short/tokens/placeholder" + ("" if have_body else " (NOT APPLIED: no body flags)")),
        ("P1 non-fork", int(rep.p1.sum()), n_sk(rep.p1), "fork = true removed"),
        ("  - keyword (Gao list)", int((rep.p1 & rep.kw_gao).sum()), n_sk(rep.p1 & rep.kw_gao), "name/description token"),
        ("  - keyword (extension)", int((rep.p1 & ~rep.kw_gao & rep.kw_ext).sum()), n_sk(rep.p1 & ~rep.kw_gao & rep.kw_ext), "marketplace|plugins|catalog(ue)|library|hub"),
        ("  - skills affix", int((rep.p1 & ~rep.kw_gao & ~rep.kw_ext & rep.kw_affix).sum()), n_sk(rep.p1 & ~rep.kw_gao & ~rep.kw_ext & rep.kw_affix), "name has skills as affix"),
        ("  - over Tukey fence", int((rep.p1 & ~(rep.kw_gao | rep.kw_ext | rep.kw_affix) & rep.over_fence).sum()), n_sk(rep.p1 & ~(rep.kw_gao | rep.kw_ext | rep.kw_affix) & rep.over_fence), f"distinct names > {fence:.1f}"),
        ("  - language null rule", int((rep.p1 & ~(rep.kw_gao | rep.kw_ext | rep.kw_affix | rep.over_fence) & rep.lang_null_rule).sum()), n_sk(rep.p1 & ~(rep.kw_gao | rep.kw_ext | rep.kw_affix | rep.over_fence) & rep.lang_null_rule), "language null, no canonical, >=2 skills"),
        ("P2 project repositories", int(rep.p2.sum()), n_sk(rep.p2), "P1 minus collection rules"),
        ("P2 with Gao rules only", int(rep.p2_gao_only.sum()), n_sk(rep.p2_gao_only), "sensitivity"),
        ("P3 clusters collapsed", int(rep.p3.sum()), n_sk(rep.p3), f"identical fingerprint or Jaccard>={JACCARD} with >={MIN_SHARED} shared"),
        ("bulk flag (within P1; all are over the fence)", int((rep.p1 & rep.bulk).sum()), n_sk(rep.p1 & rep.bulk), "sensitivity, not excluded"),
    ]
    pd.DataFrame(cascade, columns=["step", "repositories", "skills", "rule"]).to_csv(f"{args.out}/cascade.csv", index=False)
    print(pd.DataFrame(cascade, columns=["step", "repositories", "skills", "rule"]).to_string(index=False))

    # concentration
    top = rep.sort_values("n_skills_all", ascending=False)
    conc = {f"top{k}_share_of_skills": round(float(top.n_skills_all.head(k).sum() / top.n_skills_all.sum()), 4) for k in (1, 10, 100)}
    conc["largest_repo"] = top.iloc[0].repo
    thresholds = {"seed": SEED, "tukey_fence": fence, "q1": float(q1), "q3": float(q3), "boilerplate_N": n_boiler,
                  "boilerplate_N_sensitivity": [n_lo, n_hi], "boilerplate_hashes": len(boiler),
                  "clusters_in_P2": int(rep.loc[rep.p2].cluster.nunique()), "body_flags_applied": have_body, **conc}
    with open(f"{args.out}/thresholds.json", "w") as fh:
        json.dump(thresholds, fh, indent=2)
    print(json.dumps(thresholds, indent=2))

    cols = ["repo", "owner", "fork", "language", "stars", "n_skills_all", "n_skills", "n_names", "n_dirs", "has_canonical",
            "kw_gao", "kw_ext", "kw_affix", "over_fence", "lang_null_rule", "collection", "bulk",
            "p1", "p2", "p2_gao_only", "p3", "cluster", "cluster_size", "first_commit"]
    rep[cols].to_parquet(f"{args.out}/working_set.parquet", index=False)
    con.execute(f"""COPY (SELECT repo, path, libdir, file_sha, location_class, name, description, excluded, x_short, x_tokens,
                         x_placeholder, dmi, boilerplate, first_commit_at FROM s)
                    TO '{args.out}/skills.parquet' (FORMAT parquet, COMPRESSION zstd)""")
    print("written:", f"{args.out}/working_set.parquet", f"{args.out}/skills.parquet", f"{args.out}/cascade.csv", f"{args.out}/thresholds.json")


if __name__ == "__main__":
    main()
