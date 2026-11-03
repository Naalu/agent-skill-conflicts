"""For every dropped-twin path found by src/fetch_trees.py, ask GitHub whether that file existed at that path before
the GitSkills snapshot ended (2026-07-20 22:26 UTC). If it did, the search failed to return a byte-identical copy
that was there (a real drop); if the first commit touching the path is later, the copy was added after July.

Reads  data/private/validation/copy_check.csv (dropped_twin_paths column)
Writes data/private/validation/twin_verdicts.csv  one row per path: first_commit_at_path, existed_in_july
Prints the two totals the run-log rule needs. One API call per path. Usage: GITHUB_TOKEN=... uv run python src/check_twins.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

API = "https://api.github.com"
SNAPSHOT_END = "2026-07-20T22:26:00Z"


def get(url: str, token: str):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                               "User-Agent": "gitskills-msr2027-validation"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if int(r.headers.get("X-RateLimit-Remaining", "1000")) < 50:
                    time.sleep(max(0, int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - time.time()) + 1)
                return json.load(r), r.status
        except urllib.error.HTTPError as e:
            if e.code in (404, 451, 409):
                return None, e.code
            if e.code in (403, 429):
                time.sleep(60 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError:
            time.sleep(10 * (attempt + 1))
    return None, 0


def main():
    token = os.environ.get("GITHUB_TOKEN") or sys.exit("set GITHUB_TOKEN first")
    c = pd.read_csv("data/private/validation/copy_check.csv")
    out_path = "data/private/validation/twin_verdicts.csv"
    done = pd.read_csv(out_path) if os.path.exists(out_path) else pd.DataFrame(columns=["repo", "path"])
    seen = set(zip(done.repo, done.path))
    rows = done.to_dict("records")
    for _, r in c[c.dropped_twin.fillna(0) > 0].iterrows():
        for p in str(r.dropped_twin_paths).split("|"):
            if not p or (r.repo, p) in seen:
                continue
            # commits touching this path up to the snapshot end; one hit means the file was there in July
            q = urllib.parse.urlencode({"path": p, "until": SNAPSHOT_END, "per_page": 1})
            data, st = get(f"{API}/repos/{r.repo}/commits?{q}", token)
            existed = bool(data) if st == 200 else None
            last_before = data[0]["commit"]["committer"]["date"] if data else None
            rows.append({"sid": r.sid, "repo": r.repo, "path": p, "status": st, "existed_in_july": existed,
                         "last_commit_before_snapshot": last_before})
            print(f"{r.sid:4d} {p:60s} {'in July' if existed else 'after' if existed is False else 'unknown'}", flush=True)
            pd.DataFrame(rows).to_csv(out_path, index=False)
    v = pd.DataFrame(rows)
    n = len(v)
    real = int(v.existed_in_july.fillna(False).astype(bool).sum())
    unknown = int(v.existed_in_july.isna().sum())
    print(f"\n{n} dropped-twin paths: {real} existed before the snapshot (real drops), {n - real - unknown} added after, "
          f"{unknown} unknown")
    by = v.groupby("sid").existed_in_july.apply(lambda x: int(x.fillna(False).astype(bool).sum()))
    print("real drops by repository:", by[by > 0].to_dict())


if __name__ == "__main__":
    main()
