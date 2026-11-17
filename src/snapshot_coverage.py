"""Exact coverage of the dataset on the validation sample, as of the snapshot date.

For each of the 200 sampled repositories: the last default-branch commit before 2026-07-20T22:26Z and the
recursive tree at that commit (2 REST calls), compared with ALL of the dataset's rows for the repository (every
filename variant, valid or not, from data/interim/slim). This replaces the estimates from check_twins.py and
check_unique_drops.py, which compared against valid skills only and dated paths by "any commit before".

Counts are for SKILL.md files under a repository-root agent directory (.<agent>/skills/<folder>/SKILL.md), the
population our study uses, and separately for every file named SKILL.md anywhere in the tree (the dataset's own
discovery target). A file "at the snapshot but not in the dataset" is split by whether its blob SHA is a file_sha
the dataset holds for the same repository (identical copy missing) or not (content missing).

Writes data/private/validation/snapshot_coverage.csv and prints the totals.
Usage: GITHUB_TOKEN=... uv run python src/snapshot_coverage.py
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import duckdb
import pandas as pd

API = "https://api.github.com"
SNAPSHOT_END = "2026-07-20T22:26:00Z"
ROOT_SKILL = re.compile(r"^\.[A-Za-z0-9_\-]+/skills/[^/]+/SKILL\.md$")
CACHE = "data/private/validation/snapshot"


def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                               "User-Agent": "gitskills-msr2027-validation"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if int(r.headers.get("X-RateLimit-Remaining", "1000")) < 50:
                    time.sleep(max(0, int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - time.time()) + 1)
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


def snapshot_tree(repo, token):
    path = f"{CACHE}/{repo.replace('/', '__')}.json"
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    commits, st = get(f"{API}/repos/{repo}/commits?until={SNAPSHOT_END}&per_page=1", token)
    out = {"repo": repo, "status": st, "commit": None, "date": None, "truncated": None, "blobs": None}
    if commits:
        out["commit"] = commits[0]["sha"]
        out["date"] = commits[0]["commit"]["committer"]["date"]
        tree, _ = get(f"{API}/repos/{repo}/git/trees/{out['commit']}?recursive=1", token)
        if tree:
            out["truncated"] = tree.get("truncated", False)
            out["blobs"] = {t["path"]: t["sha"] for t in tree.get("tree", []) if t.get("type") == "blob"
                            and t["path"].rsplit("/", 1)[-1].lower() == "skill.md"}
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
    rows = []
    for _, s in sample.iterrows():
        t = snapshot_tree(s.repo, token)
        d = ds[ds.repo == s.repo]
        d_paths = set(d.path)
        d_shas = set(d.file_sha)
        rec = {"sid": s.sid, "repo": s.repo, "status": t["status"], "snapshot_commit_date": t["date"],
               "truncated": t["truncated"]}
        if t["blobs"] is None:
            rows.append(rec)
            print(f"{s.sid:4d} {s.repo}: no snapshot tree (HTTP {t['status']})", flush=True)
            continue
        for scope, keep in (("root", lambda p: bool(ROOT_SKILL.match(p))), ("any", lambda p: True)):
            snap = {p: h for p, h in t["blobs"].items() if keep(p)}
            in_ds = [p for p in snap if p in d_paths]
            miss = [p for p in snap if p not in d_paths]
            rec[f"{scope}_at_snapshot"] = len(snap)
            rec[f"{scope}_in_dataset"] = len(in_ds)
            rec[f"{scope}_missing_identical_copy"] = sum(1 for p in miss if snap[p] in d_shas)
            rec[f"{scope}_missing_content"] = sum(1 for p in miss if snap[p] not in d_shas)
            rec[f"{scope}_dataset_not_in_snapshot"] = len([p for p in d_paths if keep(p) and p not in snap])
        rows.append(rec)
        print(f"{s.sid:4d} {s.repo}: root {rec['root_in_dataset']}/{rec['root_at_snapshot']} in dataset", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv("data/private/validation/snapshot_coverage.csv", index=False)
    ok = out[out.root_at_snapshot.notna()]
    print(f"\n{len(ok)} of {len(out)} repositories have a tree at the snapshot commit "
          f"({int(ok.truncated.fillna(False).astype(bool).sum())} truncated)")
    for scope in ("root", "any"):
        at, ind = int(ok[f"{scope}_at_snapshot"].sum()), int(ok[f"{scope}_in_dataset"].sum())
        ic, mc = int(ok[f"{scope}_missing_identical_copy"].sum()), int(ok[f"{scope}_missing_content"].sum())
        nis = int(ok[f"{scope}_dataset_not_in_snapshot"].sum())
        print(f"{scope:4s}: {at} SKILL.md at the snapshot; {ind} in the dataset ({100 * ind / max(at, 1):.1f}%); "
              f"missing {at - ind}: identical copy of a dataset file {ic}, content not in the dataset {mc}; "
              f"repositories with any missing: {int(((ok[f'{scope}_missing_identical_copy'] + ok[f'{scope}_missing_content']) > 0).sum())}; "
              f"dataset rows not in the snapshot tree: {nis}")


if __name__ == "__main__":
    main()
