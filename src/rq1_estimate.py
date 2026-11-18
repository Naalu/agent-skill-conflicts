"""RQ1 and coverage estimates from the 2,300-repository tree-based sample.

Implements docs/runlog.md, "RQ1 tree-based sample: design" (2026-11-17). Written and tested on synthetic data before
any estimate was computed from the real sample. Inputs, all produced earlier:

  data/private/rq1/sample.parquet        the draw (src/rq1_tree_sample.py): repo, stratum, stratum_n, p2, p3, bulk
  data/private/rq1/trees/<owner>__<repo>.json
                                         SKILL.md blobs at the last commit before the snapshot end, and at the last
                                         commit before the window opened when the repository changed during it
  data/interim/slim/*.parquet            every dataset row (repo_full_name, path, file_sha), valid or not

Outputs (not committed: per_repo.csv names repositories; estimates.csv is aggregate and goes into the paper):

  data/private/rq1/per_repo.csv          one row per sampled repository with every per-repository measure
  data/private/rq1/estimates.csv         measure, domain, version, estimate, 95% interval, repositories used

Definitions (identical for the tree version and the dataset version of a repository):

  root skill file    a path matching .<agent>/skills/<folder>/SKILL.md at the repository root
  agent directory    the first path component, e.g. .claude
  skill name         <folder>, lower-cased
  mirrored name      a name present in two or more agent directories
  diverged name      a mirrored name whose copies have two or more distinct blob SHAs

Estimation: stratum weight = stratum size / repositories available in the stratum (unavailable ones are dropped and
counted); ratio estimators; 95% percentile intervals from 2,000 bootstrap replicates drawn within strata, seed
20261008. Differences (tree minus dataset) are computed within each replicate, so their intervals account for the
pairing.

    uv run python src/rq1_estimate.py
"""
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

ROOT_SKILL = re.compile(r"^(\.[A-Za-z0-9_\-]+)/skills/([^/]+)/SKILL\.md$")
SEED = 20261008
REPLICATES = 2000
OUT = "data/private/rq1"
SLIM = "data/interim/slim/*.parquet"
REFERENCE_200 = "data/private/validation/window_coverage.csv"
# Directories each product reads project skills from (as in pilot/collide/probes.py, Run 5).
PRODUCTS = {"Copilot / VS Code": [".github", ".claude", ".agents"], "Cursor": [".cursor", ".agents", ".claude", ".codex"],
            "OpenCode": [".opencode", ".claude", ".agents"], "Gemini CLI": [".gemini", ".agents"]}


# ---------------------------------------------------------------------------------------------------------------
# Per-repository measures
# ---------------------------------------------------------------------------------------------------------------

def root_files(blobs: dict | None) -> dict:
    """Keep root skill files only: path -> blob SHA."""
    return {p: s for p, s in (blobs or {}).items() if ROOT_SKILL.match(p)}


def catalog(files: dict, dirs: list | None = None) -> dict:
    """Mirroring measures for one version of one repository, optionally restricted to some agent directories."""
    copies = defaultdict(list)  # name -> [(agent directory, sha)]
    agent_dirs = set()
    for path, sha in files.items():
        agent, folder = ROOT_SKILL.match(path).groups()
        if dirs is not None and agent not in dirs:
            continue
        agent_dirs.add(agent)
        copies[folder.lower()].append((agent, sha))
    mirrored = [c for c in copies.values() if len({d for d, _ in c}) >= 2]
    diverged = [c for c in mirrored if len({s for _, s in c}) >= 2]
    return {"files": sum(len(c) for c in copies.values()), "dirs": len(agent_dirs), "names": len(copies),
            "mirrored": len(mirrored), "diverged": len(diverged)}


def measure_repo(rec: dict, ds_rows: pd.DataFrame) -> dict:
    """Everything the estimates need for one available repository."""
    end = root_files(rec["blobs"])
    ds_all = dict(zip(ds_rows.path, ds_rows.file_sha))
    ds_root = root_files(ds_all)
    ds_shas = set(ds_rows.file_sha)
    tree, data = catalog(end), catalog(ds_root)
    row = {f"tree_{k}": v for k, v in tree.items()} | {f"ds_{k}": v for k, v in data.items()}

    # coverage: files present throughout the mining window
    start = rec.get("start")
    changed = start is not None
    throughout = {p: s for p, s in end.items() if p in root_files(start.get("blobs"))} if changed else end
    missing = [p for p in throughout if p not in ds_all]
    row |= {"changed_in_window": changed,
            "truncated": bool(rec.get("truncated")) or bool(changed and start.get("truncated")),
            "throughout": len(throughout), "in_dataset": len(throughout) - len(missing),
            "missing_identical": sum(throughout[p] in ds_shas for p in missing),
            "missing_content": sum(throughout[p] not in ds_shas for p in missing)}
    for name, dirs in PRODUCTS.items():
        c = catalog(end, dirs)
        row[f"prod_{name}_any"] = c["files"] > 0
        row[f"prod_{name}_two_dirs"] = c["dirs"] >= 2
        row[f"prod_{name}_mirrored"] = c["mirrored"] > 0
        row[f"prod_{name}_diverged"] = c["diverged"] > 0
    return row


def build_per_repo(sample: pd.DataFrame, trees_dir: str, ds: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-repository table for available repositories, and the availability count per stratum."""
    by_repo = {r: g for r, g in ds.groupby("repo")}
    empty = ds.iloc[0:0]
    rows, avail = [], []
    for s in sample.itertuples():
        with open(f"{trees_dir}/{s.repo.replace('/', '__')}.json") as fh:
            rec = json.load(fh)
        ok = rec.get("commit") is not None and rec.get("blobs") is not None
        avail.append({"stratum": s.stratum, "available": ok})
        if ok:
            rows.append({"repo": s.repo, "stratum": s.stratum, "stratum_n": s.stratum_n,
                         "p2": bool(s.p2), "p3": bool(s.p3), "bulk": bool(s.bulk)}
                        | measure_repo(rec, by_repo.get(s.repo, empty)))
    per = pd.DataFrame(rows)
    a = pd.DataFrame(avail).groupby("stratum").available.agg(drawn="size", available="sum").reset_index()
    a["unavailable"] = a.drawn - a.available
    per = per.merge(a[["stratum", "available"]], on="stratum")
    per["weight"] = per.stratum_n / per.available
    return per.drop(columns="available"), a


# ---------------------------------------------------------------------------------------------------------------
# Estimates
# ---------------------------------------------------------------------------------------------------------------

def estimand_list(per: pd.DataFrame) -> list[dict]:
    """Each estimand is a ratio sum(w * num) / sum(w * den) over the sampled repositories (domain folded in)."""
    one = np.ones(len(per))
    domains = {"P2": per.p2.to_numpy(), "P3": per.p3.to_numpy(), "P2 without bulk": (per.p2 & ~per.bulk).to_numpy(),
               "P2 without truncated trees": (per.p2 & ~per.truncated).to_numpy()}
    out = []
    for dom, mask in domains.items():
        m = mask.astype(float)
        for v in ("tree", "ds"):
            out += [
                {"measure": "share of repositories with two or more agent directories", "domain": dom, "version": v,
                 "num": m * (per[f"{v}_dirs"] >= 2), "den": m * one},
                {"measure": "share of repositories with a mirrored name", "domain": dom, "version": v,
                 "num": m * (per[f"{v}_mirrored"] > 0), "den": m * one},
                {"measure": "share of repositories with a mirrored name that have a diverged name", "domain": dom,
                 "version": v, "num": m * (per[f"{v}_diverged"] > 0), "den": m * (per[f"{v}_mirrored"] > 0)},
                {"measure": "share of mirrored names that are diverged", "domain": dom, "version": v,
                 "num": m * per[f"{v}_diverged"], "den": m * per[f"{v}_mirrored"]},
            ]
    has = per.throughout > 0
    for dom, mask in {"P1": np.ones(len(per), bool), "P2": per.p2.to_numpy(),
                      "P1 without truncated trees": (~per.truncated).to_numpy()}.items():
        m = (mask & has).astype(float)
        out += [
            {"measure": "file coverage", "domain": dom, "version": "coverage",
             "num": m * per.in_dataset, "den": m * per.throughout},
            {"measure": "share of repositories complete", "domain": dom, "version": "coverage",
             "num": m * (per.in_dataset >= per.throughout), "den": m},
            {"measure": "share of missing files that are identical copies", "domain": dom, "version": "coverage",
             "num": m * per.missing_identical, "den": m * (per.missing_identical + per.missing_content)},
        ]
    for e in out:
        e["num"], e["den"] = np.asarray(e["num"], float), np.asarray(e["den"], float)
    return out


def replicate_indices(per: pd.DataFrame, reps: int = REPLICATES, seed: int = SEED) -> np.ndarray:
    """reps x n matrix of row indices, each row a resample with replacement within every stratum."""
    rng = np.random.default_rng(seed)
    blocks = []
    for _, g in per.groupby("stratum", sort=True):
        idx = g.index.to_numpy()
        blocks.append(idx[rng.integers(0, len(idx), size=(reps, len(idx)))])
    return np.concatenate(blocks, axis=1)


def estimate(per: pd.DataFrame, reps: int = REPLICATES, seed: int = SEED) -> pd.DataFrame:
    per = per.reset_index(drop=True)
    w = per.weight.to_numpy(float)
    idx = replicate_indices(per, reps, seed)
    rows, boot = [], {}
    with np.errstate(invalid="ignore", divide="ignore"):
        for e in estimand_list(per):
            wn, wd = w * e["num"], w * e["den"]
            point = wn.sum() / wd.sum() if wd.sum() > 0 else np.nan
            b = wn[idx].sum(axis=1) / wd[idx].sum(axis=1)
            key = (e["measure"], e["domain"])
            boot[key + (e["version"],)] = (point, b)
            lo, hi = np.nanpercentile(b, [2.5, 97.5]) if np.isfinite(b).any() else (np.nan, np.nan)
            rows.append({"measure": e["measure"], "domain": e["domain"], "version": e["version"],
                         "estimate": point, "ci_low": lo, "ci_high": hi, "repositories": int((e["den"] > 0).sum())})
        for (meas, dom, ver), (p_tree, b_tree) in list(boot.items()):
            if ver != "tree":
                continue
            p_ds, b_ds = boot[(meas, dom, "ds")]
            d = b_tree - b_ds
            lo, hi = np.nanpercentile(d, [2.5, 97.5]) if np.isfinite(d).any() else (np.nan, np.nan)
            n = next(r["repositories"] for r in rows if (r["measure"], r["domain"], r["version"]) == (meas, dom, "tree"))
            rows.append({"measure": meas, "domain": dom, "version": "tree minus ds", "estimate": p_tree - p_ds,
                         "ci_low": lo, "ci_high": hi, "repositories": n})
    return pd.DataFrame(rows)


def products(per: pd.DataFrame) -> pd.DataFrame:
    """Secondary: estimated numbers of P2 repositories per product directory set, tree version, point estimates."""
    p = per[per.p2]
    rows = []
    for name in PRODUCTS:
        rows.append({"product": name} | {k: round(float((p.weight * p[f"prod_{name}_{k}"]).sum()))
                                         for k in ("any", "two_dirs", "mirrored", "diverged")})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------------------------------

def load_dataset_rows(repos: list[str], slim: str = SLIM) -> pd.DataFrame:
    import duckdb
    con = duckdb.connect()
    con.register("want", pd.DataFrame({"repo": repos}))
    return con.execute(f"""SELECT repo_full_name AS repo, path, file_sha FROM read_parquet('{slim}')
                           WHERE repo_full_name IN (SELECT repo FROM want)""").fetchdf()


def main(out: str = OUT, slim: str = SLIM, reps: int = REPLICATES) -> None:
    sample = pd.read_parquet(f"{out}/sample.parquet")
    missing = [r for r in sample.repo if not os.path.exists(f"{out}/trees/{r.replace('/', '__')}.json")]
    if missing:
        sys.exit(f"{len(missing)} repositories have no cached tree; run src/rq1_tree_sample.py first")
    ds = load_dataset_rows(sample.repo.tolist(), slim)
    per, avail = build_per_repo(sample, f"{out}/trees", ds)
    per.to_csv(f"{out}/per_repo.csv", index=False)
    est = estimate(per, reps)
    est.to_csv(f"{out}/estimates.csv", index=False)

    pd.set_option("display.width", 160, "display.max_colwidth", 70, "display.max_rows", 200)
    print("Availability by stratum\n" + avail.to_string(index=False))
    print(f"\n{len(per):,} available; {int(per.changed_in_window.sum())} changed during the mining window; "
          f"{int(per.truncated.sum())} truncated trees\n")
    show = est.copy()
    for c in ("estimate", "ci_low", "ci_high"):
        show[c] = show[c].map(lambda x: f"{x:+.3f}" if pd.notna(x) else "")
    print(show.to_string(index=False))
    print("\nProduct directory sets, P2, tree version (estimated repositories)\n" + products(per).to_string(index=False))
    if os.path.exists(REFERENCE_200):
        r = pd.read_csv(REFERENCE_200)
        r = r[r.throughout > 0]
        print(f"\nFor comparison, the 200-repository validation sample: file coverage "
              f"{(r.weight * r.in_dataset).sum() / (r.weight * r.throughout).sum():.3f} over {len(r)} repositories")
    print(f"\nwritten: {out}/per_repo.csv (private), {out}/estimates.csv")


if __name__ == "__main__":
    main()
