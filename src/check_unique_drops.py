"""How many of the 'new content' paths (on GitHub, missing from the dataset, SHA unknown to the dataset) existed
before the snapshot? This separates post-July additions from files the search dropped although their content was
unique. Seeded sample of N paths from data/private/validation/copy_check.csv-era raw trees; one commits call each.
Usage: GITHUB_TOKEN=... uv run python src/check_unique_drops.py [N=150]
Writes data/private/validation/unique_verdicts.csv and prints the totals for the run log.
"""
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

API = "https://api.github.com"
SNAPSHOT_END = "2026-07-20T22:26:00Z"
ROOT_SKILL = re.compile(r"^\.[A-Za-z0-9_\-]+/skills/[^/]+/SKILL\.md$")
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
    return None, 0


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    token = os.environ.get("GITHUB_TOKEN") or sys.exit("set GITHUB_TOKEN")
    skills = pd.read_parquet("data/interim/skills.parquet", columns=["repo", "path", "file_sha"])
    cands = []
    for f in glob.glob("data/private/validation/raw/*.json"):
        with open(f) as fh:
            d = json.load(fh)
        if d["status"] != 200 or not d.get("blobs"):
            continue
        ds = skills[skills.repo == d["repo"]]
        ds_paths, ds_shas = set(ds.path), set(ds.file_sha)
        for p, sha in d["blobs"].items():
            if ROOT_SKILL.match(p) and p not in ds_paths and sha not in ds_shas:
                cands.append((d["repo"], p))
    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(cands), size=min(n, len(cands)), replace=False)
    rows = []
    for i in idx:
        repo, p = cands[i]
        q = urllib.parse.urlencode({"path": p, "until": SNAPSHOT_END, "per_page": 1})
        data, st = get(f"{API}/repos/{repo}/commits?{q}", token)
        existed = bool(data) if st == 200 else None
        rows.append({"repo": repo, "path": p, "status": st, "existed_in_july": existed,
                     "last_commit_before_snapshot": data[0]["commit"]["committer"]["date"] if data else None})
        print(f"{p:70s} {'in July' if existed else 'after' if existed is False else 'unknown'}", flush=True)
        pd.DataFrame(rows).to_csv("data/private/validation/unique_verdicts.csv", index=False)
    v = pd.DataFrame(rows)
    real = int(v.existed_in_july.fillna(False).astype(bool).sum())
    print(f"\n{len(cands)} unique-content paths missing from the dataset; sampled {len(v)}: {real} existed before the "
          f"snapshot ({100 * real / len(v):.1f}%), {len(v) - real} added after. Scaled: about {real / len(v) * len(cands):.0f} "
          f"dropped unique files across the 181 repositories, against {len(skills[skills.repo.isin({c[0] for c in cands})])} dataset rows in the repositories with any.")


if __name__ == "__main__":
    main()
