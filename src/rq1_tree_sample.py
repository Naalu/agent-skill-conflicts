"""Draw the RQ1 tree-based sample and fetch each repository's SKILL.md files as of the dataset snapshot.

Design: docs/runlog.md, "RQ1 tree-based sample: design" (2026-11-17). In short: 2,300 repositories from P1,
stratified by what the dataset shows for them, seed 20261008. For each one, the recursive tree at the last
default-branch commit before the snapshot ended (2026-07-20T22:26Z) gives every SKILL.md path with its git blob SHA,
which is what GitSkills stores as file_sha. Where that commit falls inside the mining window, the tree at the last
commit before the window opened (2026-07-09T17:26Z) is fetched as well, so the coverage figure can be restricted to
files present throughout. This script only draws and fetches; the estimates come from src/rq1_estimate.py.

    export GITHUB_TOKEN=$(gh auth token)
    uv run python src/rq1_tree_sample.py            # draw (if not drawn yet), then fetch
    uv run python src/rq1_tree_sample.py --draw-only

Cost: 2 REST calls per repository, 4 where the repository changed during the window; about 6,000 in all, so the run
pauses once for the hourly limit of 5,000. Every response is cached in data/private/rq1/trees/, so the script can
be stopped and started again; a repository whose requests failed is not cached and is retried on the next run.
"""
import argparse
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.request

import numpy as np
import pandas as pd

API = "https://api.github.com"
WINDOW_START = "2026-07-09T17:26:00Z"
SNAPSHOT_END = "2026-07-20T22:26:00Z"
SEED = 20261008
OUT = "data/private/rq1"
# stratum -> repositories to draw. Strata are defined in stratum() below.
ALLOCATION = {"p2_1dir_1name": 400, "p2_1dir_2plus": 800, "p2_2plus_dirs": 800, "not_p2": 300}


def stratum(w: pd.DataFrame) -> pd.Series:
    """Stratum of each P1 repository, from the dataset's own view of it (valid skills, working set v1)."""
    s = pd.Series("p2_1dir_1name", index=w.index)
    s[(w.n_dirs == 1) & (w.n_names >= 2)] = "p2_1dir_2plus"
    s[w.n_dirs >= 2] = "p2_2plus_dirs"
    s[~w.p2] = "not_p2"
    return s


def draw(out: str = OUT) -> pd.DataFrame:
    """Stratified simple random sample without replacement from P1; weight = stratum size / number drawn."""
    w = pd.read_parquet("data/interim/working_set.parquet")
    w = w[w.p1].sort_values("repo").reset_index(drop=True)
    w["stratum"] = stratum(w)
    rng = np.random.default_rng(SEED)
    parts = []
    for name, n in ALLOCATION.items():
        cell = w[w.stratum == name]
        take = min(n, len(cell))
        part = w.loc[rng.choice(cell.index.to_numpy(), size=take, replace=False)].copy()
        part["stratum_n"], part["weight"] = len(cell), len(cell) / take
        parts.append(part)
        print(f"stratum {name}: {take} of {len(cell):,}")
    s = pd.concat(parts).sort_values("repo").reset_index(drop=True)
    cols = ["repo", "stratum", "stratum_n", "weight", "p2", "p3", "n_dirs", "n_names", "n_skills", "over_fence", "bulk"]
    os.makedirs(out, exist_ok=True)
    s[cols].to_parquet(f"{out}/sample.parquet", index=False)
    s[cols].to_csv(f"{out}/sample.csv", index=False)
    print(f"{len(s):,} repositories written to {out}/sample.csv")
    return s[cols]


def get(url: str, token: str):
    """GET a GitHub REST URL. Returns (json, status); (None, 404/409/451) when the thing is gone; (None, 0) on failure."""
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                               "User-Agent": "gitskills-msr2027-rq1"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = json.loads(r.read())
                if int(r.headers.get("X-RateLimit-Remaining", "1000")) < 20:
                    wait = max(0, int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - time.time()) + 5
                    print(f"  rate limit reached; waiting {wait / 60:.0f} minutes", flush=True)
                    time.sleep(wait)
                return body, r.status
        except urllib.error.HTTPError as e:
            if e.code in (404, 409, 451):
                return None, e.code
            if e.code in (403, 429):  # primary or secondary rate limit
                reset = e.headers.get("X-RateLimit-Reset") if e.headers.get("X-RateLimit-Remaining") == "0" else None
                time.sleep(max(0, int(reset) - time.time()) + 5 if reset else 60 * (attempt + 1))
                continue
            if e.code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, http.client.HTTPException, ConnectionError, TimeoutError, json.JSONDecodeError):
            time.sleep(10 * (attempt + 1))  # dropped or cut-off response: wait and ask again
    return None, 0


def tree_before(repo: str, until: str, token: str) -> dict | None:
    """SKILL.md blobs in the tree at the last default-branch commit before `until`. None if a request failed."""
    commits, st = get(f"{API}/repos/{repo}/commits?until={until}&per_page=1", token)
    if st == 0:
        return None
    out = {"status": st, "commit": None, "date": None, "truncated": None, "blobs": None}
    if commits:
        out["commit"] = commits[0]["sha"]
        out["date"] = commits[0]["commit"]["committer"]["date"]
        tree, st2 = get(f"{API}/repos/{repo}/git/trees/{out['commit']}?recursive=1", token)
        if st2 == 0:
            return None
        if tree:
            out["truncated"] = tree.get("truncated", False)
            out["blobs"] = {t["path"]: t["sha"] for t in tree.get("tree", []) if t.get("type") == "blob"
                            and t["path"].rsplit("/", 1)[-1].lower() == "skill.md"}
    return out


def fetch(sample: pd.DataFrame, token: str, out: str = OUT) -> None:
    cache = f"{out}/trees"
    os.makedirs(cache, exist_ok=True)
    done = failed = gone = in_window = 0
    for i, repo in enumerate(sample.repo, 1):
        path = f"{cache}/{repo.replace('/', '__')}.json"
        if os.path.exists(path):
            done += 1
            continue
        end = tree_before(repo, SNAPSHOT_END, token)
        if end is None:
            failed += 1
            print(f"{i:5d} {repo}: request failed, will retry on the next run", flush=True)
            continue
        rec = {"repo": repo, **end, "start": None}
        if end["date"] and end["date"] >= WINDOW_START:  # changed during the mining window: tree at its start too
            start = tree_before(repo, WINDOW_START, token)
            if start is None:
                failed += 1
                print(f"{i:5d} {repo}: request failed, will retry on the next run", flush=True)
                continue
            rec["start"] = start
            in_window += 1
        with open(path, "w") as fh:
            json.dump(rec, fh)
        done += 1
        gone += end["blobs"] is None
        n = "unavailable" if end["blobs"] is None else f"{len(end['blobs'])} SKILL.md"
        print(f"{i:5d} {repo}: {n}{' (changed in window)' if rec['start'] else ''}", flush=True)
    print(f"\n{done:,} of {len(sample):,} repositories cached; fetched this run: {gone} unavailable, "
          f"{in_window} changed during the mining window; {failed} failed")
    if failed:
        print("Run the same command again to retry the failed ones.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--draw-only", action="store_true", help="draw the sample and stop")
    a = ap.parse_args()
    if os.path.exists(f"{OUT}/sample.parquet"):
        sample = pd.read_parquet(f"{OUT}/sample.parquet")
        print(f"using the sample already drawn: {len(sample):,} repositories")
    else:
        sample = draw()
    if a.draw_only:
        return
    token = os.environ.get("GITHUB_TOKEN") or sys.exit("set GITHUB_TOKEN first: export GITHUB_TOKEN=$(gh auth token)")
    fetch(sample, token)


if __name__ == "__main__":
    main()
