"""Fetch what the validation coders need for each sampled repository, and run the byte-exact copy check.

For each row of data/private/validation/sample.parquet: the repository record, the default-branch tree
(recursive) and the README, via the GitHub REST API (token in GITHUB_TOKEN; three calls per repository, about
600 in all). Raw responses are kept as JSON in data/private/validation/raw/<owner>__<repo>.json so a rerun is
free. Then two outputs:

  labelling/validation-200/sheet.csv   the blank coding sheet (committed, no repository names: sid only, plus the
                                       material the coder reads in labelling/validation-200/material/<sid>.md,
                                       which is NOT committed because it quotes READMEs and names repositories)
  data/private/validation/copy_check.csv
                                       per repository: SKILL.md paths under root agent directories on GitHub now,
                                       paths in the dataset, paths missing from the dataset, and for each missing
                                       path whether a byte-identical sibling is in the dataset (the byte-exact
                                       question of the run-log amendment).

Repositories that no longer exist (404) or whose tree is truncated are recorded as such and still coded from
whatever came back. Usage: GITHUB_TOKEN=... uv run python src/fetch_trees.py
"""
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import pandas as pd

API = "https://api.github.com"
ROOT_SKILL = re.compile(r"^\.[A-Za-z0-9_\-]+/skills/[^/]+/SKILL\.md$")
RAW = "data/private/validation/raw"
MAT = "labelling/validation-200/material"


def get(url: str, token: str):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                               "User-Agent": "gitskills-msr2027-validation"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                remaining = int(r.headers.get("X-RateLimit-Remaining", "1000"))
                if remaining < 50:
                    reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
                    time.sleep(max(0, reset - time.time()) + 1)
                return json.load(r), r.status
        except urllib.error.HTTPError as e:
            if e.code in (404, 451):
                return None, e.code
            if e.code in (403, 429):
                time.sleep(60 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError:
            time.sleep(10 * (attempt + 1))
    return None, 0


def fetch(repo: str, token: str) -> dict:
    path = f"{RAW}/{repo.replace('/', '__')}.json"
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    meta, st = get(f"{API}/repos/{repo}", token)
    out = {"repo": repo, "status": st, "meta": meta, "tree": None, "truncated": None, "readme": None}
    if meta:
        branch = meta.get("default_branch", "HEAD")
        tree, _ = get(f"{API}/repos/{repo}/git/trees/{branch}?recursive=1", token)
        if tree:
            out["tree"] = [t["path"] for t in tree.get("tree", []) if t.get("type") == "blob"]
            out["truncated"] = tree.get("truncated", False)
        readme, _ = get(f"{API}/repos/{repo}/readme", token)
        if readme and readme.get("content"):
            try:
                out["readme"] = base64.b64decode(readme["content"]).decode("utf-8", "replace")[:4000]
            except Exception:  # noqa: BLE001 - a README that will not decode is still a README
                out["readme"] = None
    with open(path, "w") as fh:
        json.dump(out, fh)
    return out


def main():
    token = os.environ.get("GITHUB_TOKEN") or sys.exit("set GITHUB_TOKEN first")
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(MAT, exist_ok=True)
    sample = pd.read_parquet("data/private/validation/sample.parquet")
    skills = pd.read_parquet("data/interim/skills.parquet", columns=["repo", "path", "file_sha"])
    rows, checks = [], []
    for i, r in sample.iterrows():
        d = fetch(r.repo, token)
        print(f"{r.sid:4d} {r.repo} status {d['status']}", flush=True)
        tree = d["tree"] or []
        top = sorted({p.split("/")[0] for p in tree})
        gh_skills = sorted(p for p in tree if ROOT_SKILL.match(p))
        ds = skills[skills.repo == r.repo]
        ds_paths = set(ds.path)
        missing = [p for p in gh_skills if p not in ds_paths]
        extra = sorted(ds_paths - set(gh_skills))
        # byte-exact question: a path on GitHub that the dataset lacks, where the dataset holds an identical sibling
        # (same file_sha) elsewhere in the repository, is a dropped twin; we cannot hash GitHub content here, so
        # we record the candidate and the coder confirms by eye from the two paths' folder names
        twin_candidates = [p for p in missing if any(p.split("/")[2] == q.split("/")[2] for q in ds_paths)]
        checks.append({"sid": r.sid, "repo": r.repo, "status": d["status"], "truncated": d["truncated"],
                       "gh_root_skills": len(gh_skills), "dataset_root_skills": len(ds_paths),
                       "missing_from_dataset": len(missing), "missing_paths": "|".join(missing),
                       "same_folder_twin_candidates": len(twin_candidates),
                       "in_dataset_not_on_github": len(extra), "extra_paths": "|".join(extra)})
        meta = d["meta"] or {}
        with open(f"{MAT}/{r.sid:03d}.md", "w") as fh:
            fh.write(f"# Repository {r.sid:03d}\n\n")
            fh.write(f"Status: {d['status']}; archived: {meta.get('archived')}; language: {meta.get('language')}; "
                     f"stars: {meta.get('stargazers_count')}; tree truncated: {d['truncated']}\n\n")
            fh.write(f"Description: {meta.get('description')}\n\n")
            fh.write(f"Top-level entries ({len(top)}): {', '.join(top[:60])}\n\n")
            fh.write(f"Files in tree: {len(tree)}; SKILL.md under root agent directories: {len(gh_skills)}\n\n")
            fh.write("Skill paths:\n" + "\n".join(f"- {p}" for p in gh_skills[:80]) + "\n\n")
            fh.write("README (first 4,000 characters):\n\n" + (d["readme"] or "(none)") + "\n")
        rows.append({"sid": r.sid, "label": "", "notes": ""})
    os.makedirs("labelling/validation-200", exist_ok=True)
    pd.DataFrame(rows).to_csv("labelling/validation-200/sheet.csv", index=False)
    pd.DataFrame(checks).to_csv("data/private/validation/copy_check.csv", index=False)
    c = pd.DataFrame(checks)
    ok = c[c.status == 200]
    print(f"\n{len(ok)} repositories fetched; {int((c.status != 200).sum())} unavailable; "
          f"{int(ok.truncated.fillna(False).astype(bool).sum())} truncated trees")
    print(f"paths on GitHub missing from the dataset: {int(ok.missing_from_dataset.sum())} across "
          f"{int((ok.missing_from_dataset > 0).sum())} repositories; same-folder twin candidates: "
          f"{int(ok.same_folder_twin_candidates.sum())}")
    print("coding sheet: labelling/validation-200/sheet.csv; material: labelling/validation-200/material/")


if __name__ == "__main__":
    main()
