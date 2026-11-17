"""Robustness check for snapshot_coverage.py: files that changed during the mining window.

GitSkills searched between 2026-07-09T17:26Z and 2026-07-20T22:26Z. snapshot_coverage.py compares the dataset with
each repository's tree at the END of that window, so a file added after the search reached its size bucket counts as
missing although the search could not have seen it. Here a file counts as missing only if it is present in the trees
at BOTH ends of the window (it existed throughout) and absent from the dataset. Only repositories whose snapshot
commit falls inside the window need the extra tree (2 calls each); the rest are unchanged across the window.

Reads data/private/validation/snapshot/*.json (cache from snapshot_coverage.py), sample.csv, data/interim/slim.
Writes data/private/validation/window_coverage.csv. Usage: GITHUB_TOKEN=... uv run python src/window_check.py
"""
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import duckdb
import numpy as np
import pandas as pd

API = "https://api.github.com"
WINDOW_START = "2026-07-09T17:26:00Z"
ROOT_SKILL = re.compile(r"^\.[A-Za-z0-9_\-]+/skills/[^/]+/SKILL\.md$")
CACHE = "data/private/validation/snapshot_start"
SEED = 20261008


def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                               "User-Agent": "gitskills-msr2027-validation"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r), r.status
        except urllib.error.HTTPError as e:
            if e.code in (404, 409, 451):
                return None, e.code
            if e.code in (403, 429):
                time.sleep(60 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError:
            time.sleep(10 * (attempt + 1))
    return None, 0


def start_tree(repo, token):
    path = f"{CACHE}/{repo.replace('/', '__')}.json"
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    commits, st = get(f"{API}/repos/{repo}/commits?until={WINDOW_START}&per_page=1", token)
    out = {"repo": repo, "status": st, "blobs": None}
    if commits:
        tree, _ = get(f"{API}/repos/{repo}/git/trees/{commits[0]['sha']}?recursive=1", token)
        if tree:
            out["blobs"] = {t["path"]: t["sha"] for t in tree.get("tree", []) if t.get("type") == "blob"
                            and t["path"].rsplit("/", 1)[-1].lower() == "skill.md"}
    else:
        out["blobs"] = {}  # repository created inside the window: nothing existed throughout
    with open(path, "w") as fh:
        json.dump(out, fh)
    return out


def main():
    token = os.environ.get("GITHUB_TOKEN") or sys.exit("set GITHUB_TOKEN")
    os.makedirs(CACHE, exist_ok=True)
    sample = pd.read_csv("data/private/validation/sample.csv")
    repos = ",".join("'" + r.replace("'", "''") + "'" for r in sample.repo)
    ds = duckdb.connect().execute(f"""SELECT repo_full_name AS repo, path, file_sha
        FROM read_parquet('data/interim/slim/*.parquet') WHERE repo_full_name IN ({repos})""").fetchdf()
    end = {}
    for f in glob.glob("data/private/validation/snapshot/*.json"):
        with open(f) as fh:
            d = json.load(fh)
        end[d["repo"]] = d
    rows = []
    for _, s in sample.iterrows():
        e = end.get(s.repo)
        if not e or e.get("blobs") is None:
            continue
        e_root = {p: h for p, h in e["blobs"].items() if ROOT_SKILL.match(p)}
        if not e_root:
            continue
        in_window = e["date"] >= WINDOW_START
        if in_window:
            st = start_tree(s.repo, token)
            if st["blobs"] is None:
                continue
            both = {p: h for p, h in e_root.items() if st["blobs"].get(p) is not None}
        else:
            both = e_root
        d = ds[ds.repo == s.repo]
        dp, dsha = set(d.path), set(d.file_sha)
        miss = [p for p in both if p not in dp]
        rows.append({"sid": s.sid, "repo": s.repo, "weight": s.weight, "pred": s.pred, "band": s.band,
                     "changed_in_window": in_window, "throughout": len(both), "in_dataset": len(both) - len(miss),
                     "missing_identical": sum(1 for p in miss if both[p] in dsha),
                     "missing_content": sum(1 for p in miss if both[p] not in dsha)})
        print(f"{s.sid:4d} {s.repo}: {len(both) - len(miss)}/{len(both)}{' (window)' if in_window else ''}", flush=True)
    v = pd.DataFrame(rows)
    v.to_csv("data/private/validation/window_coverage.csv", index=False)
    v = v[v.throughout > 0]
    ratio = lambda g: float(np.sum(g.weight * g.in_dataset) / np.sum(g.weight * g.throughout))
    rng = np.random.default_rng(SEED)
    cells = [g for _, g in v.groupby(["pred", "band"])]
    boot = [ratio(pd.concat([g.sample(len(g), replace=True, random_state=int(rng.integers(1e9))) for g in cells]))
            for _ in range(2000)]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f"\n{len(v)} repositories; {int(v.changed_in_window.sum())} changed during the mining window")
    print(f"files present throughout the window: {int(v.throughout.sum())}; in the dataset {int(v.in_dataset.sum())} "
          f"({100 * v.in_dataset.sum() / v.throughout.sum():.1f}% unweighted); missing identical copy "
          f"{int(v.missing_identical.sum())}, missing content {int(v.missing_content.sum())}")
    print(f"weighted file coverage {ratio(v):.3f} (95% CI {lo:.3f} to {hi:.3f}); "
          f"repositories complete {np.sum(v.weight * (v.in_dataset >= v.throughout)) / np.sum(v.weight):.3f} (weighted)")


if __name__ == "__main__":
    main()
