#!/usr/bin/env python3
"""Fetch the first and last commit date of each flagged SKILL.md occurrence from the GitHub REST API.

Why: GitSkills carries commit history for one representative copy per distinct content (458,548 files).
The born-stale analysis needs the date each *occurrence* entered its repository.

Usage:
    export GITHUB_TOKEN=<a fine-grained token with public-repo read access>
    python fetch_first_commits.py flagged_occurrences.csv commit_dates.csv

Input  CSV columns: repo, path, file_sha, first_ret   (written by the pilot)
Output CSV columns: repo, path, file_sha, first_commit_at, last_commit_at, n_commits, status

The script is resumable: rows already present in the output file are skipped.
Two requests per file (newest commit, then the last page for the oldest); about 5,000 requests/hour per token.
Only commit timestamps are stored. No author names, logins or e-mail addresses are requested or written.
"""
import csv, os, re, sys, time, urllib.parse, urllib.request, urllib.error, json

API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")


def gh_get(url):
    """GET one API URL; return (json, headers). Sleeps through rate limits; returns (None, None) on 404/409/451."""
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "gitskills-born-stale"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r), r.headers
        except urllib.error.HTTPError as e:
            if e.code in (404, 409, 451):
                return None, None
            reset = e.headers.get("X-RateLimit-Reset")
            if e.code in (403, 429) and reset:
                time.sleep(max(5, int(reset) - int(time.time()) + 5))
            else:
                time.sleep(2 ** attempt)
        except Exception:
            time.sleep(2 ** attempt)
    return None, None


def commit_dates(repo, path):
    """Return (first_commit_at, last_commit_at, n_commits) for one file on the default branch."""
    q = urllib.parse.urlencode({"path": path, "per_page": 1})
    newest, headers = gh_get(f"{API}/repos/{repo}/commits?{q}")
    if not newest:
        return None, None, 0
    last_at = newest[0]["commit"]["committer"]["date"]
    m = re.search(r'[?&]page=(\d+)>; rel="last"', headers.get("Link", "") or "")
    n = int(m.group(1)) if m else 1
    if n == 1:
        return last_at, last_at, 1
    oldest, _ = gh_get(f"{API}/repos/{repo}/commits?{q}&page={n}")
    first_at = oldest[0]["commit"]["committer"]["date"] if oldest else None
    return first_at, last_at, n


def main(src, dst):
    if not TOKEN:
        sys.exit("Set GITHUB_TOKEN first.")
    done = set()
    if os.path.exists(dst):
        with open(dst, newline="") as f:
            done = {(r["repo"], r["path"]) for r in csv.DictReader(f)}
    new_file = not os.path.exists(dst)
    with open(src, newline="") as fin, open(dst, "a", newline="") as fout:
        w = csv.writer(fout)
        if new_file:
            w.writerow(["repo", "path", "file_sha", "first_commit_at", "last_commit_at", "n_commits", "status"])
        for i, r in enumerate(csv.DictReader(fin)):
            if (r["repo"], r["path"]) in done:
                continue
            first_at, last_at, n = commit_dates(r["repo"], r["path"])
            w.writerow([r["repo"], r["path"], r["file_sha"], first_at, last_at, n, "ok" if n else "missing"])
            if i % 200 == 0:
                fout.flush(); print(i, r["repo"], flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
