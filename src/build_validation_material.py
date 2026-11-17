"""Rebuild the validation coders' material from the repository as it was at the dataset snapshot, with translations.

Why a second version: the first material (src/fetch_trees.py) showed each repository as it is today, not as it was
when GitSkills mined it, listed only SKILL.md files under root agent directories (so a top-level skills/ folder, the
usual sign of a collection, was invisible), quoted the first 4,000 raw characters of the README (often nothing but
badges and HTML), and gave non-English material untranslated, contrary to the language rule in docs/runlog.md
(2026-10-15). This version:

  - reads the tree and README at the snapshot commit already recorded by src/snapshot_coverage.py (the last
    default-branch commit before 2026-07-20T22:26Z), two REST calls per repository, cached;
  - lists every SKILL.md path, split into "under a root agent directory" and "elsewhere";
  - cleans the README (HTML tags, images and badge-only lines removed, long code blocks shortened) before taking the
    first 4,000 characters;
  - detects the language of the description and README with lingua (confidence >= 0.60, as in the RQ2 rule) and
    adds a DeepL EN-US translation below the original when either is not English. One run, one service, both
    coders read the same file; a sidecar records service and date;
  - for repositories with no snapshot commit (deleted or private now), shows the dataset's own description and skill
    paths and says so.

The first-version material is moved to data/private/validation/material-v1/ (git-ignored) before anything is written.

Usage (from the repository root, with both keys in the environment, never in a file):
    export GITHUB_TOKEN=$(gh auth token)
    export DEEPL_AUTH_KEY=...
    uv run --with deepl --with lingua-language-detector python src/build_validation_material.py
"""
import datetime as dt
import http.client
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request

import pandas as pd

API = "https://api.github.com"
ROOT_SKILL = re.compile(r"^\.[A-Za-z0-9_\-]+/skills/[^/]+/SKILL\.md$")
SNAP = "data/private/validation/snapshot"
CURRENT = "data/private/validation/raw"
CACHE = "data/private/validation/material_raw"
MAT = "labelling/validation-200/material"
OLD = "data/private/validation/material-v1"
SIDECAR = "data/private/validation/material_translation.json"
README_CHARS = 4000
LIST_MAX = 60


def get(url, token, raw=False):
    accept = "application/vnd.github.raw+json" if raw else "application/vnd.github+json"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": accept,
                                               "User-Agent": "gitskills-msr2027-validation"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if int(r.headers.get("X-RateLimit-Remaining", "1000")) < 50:
                    time.sleep(max(0, int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - time.time()) + 1)
                body = r.read()
                return (body.decode("utf-8", "replace") if raw else json.loads(body)), r.status
        except urllib.error.HTTPError as e:
            if e.code in (404, 409, 451):
                return None, e.code
            if e.code in (403, 429):
                time.sleep(60 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, http.client.HTTPException, ConnectionError, TimeoutError):
            time.sleep(10 * (attempt + 1))  # dropped or cut-off response: wait and ask again
    sys.exit(f"gave up after 5 attempts: {url}")


def at_snapshot(repo, commit, token):
    path = f"{CACHE}/{repo.replace('/', '__')}.json"
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    tree, _ = get(f"{API}/repos/{repo}/git/trees/{commit}?recursive=1", token)
    readme, _ = get(f"{API}/repos/{repo}/readme?ref={commit}", token, raw=True)
    out = {"repo": repo, "commit": commit,
           "paths": [t["path"] for t in (tree or {}).get("tree", []) if t.get("type") == "blob"],
           "truncated": (tree or {}).get("truncated"), "readme": readme}
    with open(path, "w") as fh:
        json.dump(out, fh)
    return out


def read_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return json.load(fh)


def clean_readme(text):
    if not text:
        return ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    def shorten(m):  # keep install commands and short examples, cut long listings
        lines = m.group(0).splitlines()
        return "\n".join(lines[:9] + ["    [...]", lines[-1]]) if len(lines) > 10 else m.group(0)
    text = re.sub(r"```.*?```", shorten, text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)            # markdown images
    text = re.sub(r"\[\s*\]\([^)]*\)", "", text)                 # links left empty by removed images (badges)
    text = re.sub(r"<img[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?[A-Za-z][^>]*>", "", text)               # other HTML tags, keep inner text
    text = "\n".join(l.rstrip() for l in text.splitlines() if not re.fullmatch(r"[\s|·•\-_*=]*", l) or l == "")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:README_CHARS]


def main():
    token = os.environ.get("GITHUB_TOKEN") or sys.exit("set GITHUB_TOKEN first")
    key = os.environ.get("DEEPL_AUTH_KEY") or sys.exit("set DEEPL_AUTH_KEY first")
    try:
        import deepl
        from lingua import LanguageDetectorBuilder
    except ImportError:
        sys.exit("run with: uv run --with deepl --with lingua-language-detector python src/build_validation_material.py")
    detector = LanguageDetectorBuilder.from_all_languages().build()
    translator = deepl.DeepLClient(key)

    def language(text):
        letters = re.sub(r"[^\w\s]", " ", text or "")
        if len(re.findall(r"[^\W\d_]", letters)) < 20:
            return "en", 1.0  # too short to judge; names and one-word descriptions stay as they are
        top = detector.compute_language_confidence_values(letters)[0]
        code = top.language.iso_code_639_1.name.lower()
        return code, round(top.value, 2)

    if os.path.isdir(MAT) and not os.path.isdir(OLD):
        shutil.move(MAT, OLD)
    os.makedirs(MAT, exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)

    sample = pd.read_parquet("data/private/validation/sample.parquet")
    skills = pd.read_parquet("data/interim/skills.parquet", columns=["repo", "path"])
    repos = pd.read_parquet("data/interim/repos.parquet")
    repos = repos.drop_duplicates("full_name").set_index("full_name")
    log, chars = [], 0
    for r in sample.sort_values("sid").itertuples():
        snap_path = f"{SNAP}/{r.repo.replace('/', '__')}.json"
        snap = read_json(snap_path) or {}
        cur_path = f"{CURRENT}/{r.repo.replace('/', '__')}.json"
        meta = (read_json(cur_path) or {}).get("meta") or {}
        known = repos.loc[r.repo] if r.repo in repos.index else {}
        description = meta.get("description") or (known.get("description") if len(known) else None)
        description = description if isinstance(description, str) else None
        primary = meta.get("language") or (known.get("language") if len(known) else None)

        if snap.get("commit"):
            d = at_snapshot(r.repo, snap["commit"], token)
            paths, readme, source = d["paths"], clean_readme(d["readme"]), f"snapshot commit of {snap['date'][:10]}"
            truncated = d["truncated"]
        else:
            paths = sorted(skills.loc[skills.repo == r.repo, "path"])
            readme, source, truncated = "", f"not on GitHub now (status {snap.get('status')}); dataset rows only", None
        skill_paths = sorted(p for p in paths if p.rsplit("/", 1)[-1].lower() == "skill.md")
        root = [p for p in skill_paths if ROOT_SKILL.match(p)]
        other = [p for p in skill_paths if not ROOT_SKILL.match(p)]
        top = sorted({p.split("/")[0] for p in paths})

        lang_d, conf_d = language(description)
        lang_r, conf_r = language(readme)
        tr_d = tr_r = None
        if description and lang_d != "en" and conf_d >= 0.60:
            tr_d = translator.translate_text(description, target_lang="EN-US").text
            chars += len(description)
        if readme and lang_r != "en" and conf_r >= 0.60:
            tr_r = translator.translate_text(readme, target_lang="EN-US",
                                             model_type="prefer_quality_optimized").text
            chars += len(readme)
        log.append({"sid": int(r.sid), "description_lang": lang_d, "description_conf": conf_d,
                    "readme_lang": lang_r, "readme_conf": conf_r,
                    "translated_description": tr_d is not None, "translated_readme": tr_r is not None})

        with open(f"{MAT}/{r.sid:03d}.md", "w", encoding="utf-8") as fh:
            fh.write(f"# Repository {r.sid:03d}\n\n")
            fh.write(f"Shown as of: {source}. Primary language: {primary}; "
                     f"tree truncated: {truncated}\n\n")
            fh.write(f"Description: {description}\n")
            if tr_d:
                fh.write(f"Description, machine translation ({lang_d} to English, DeepL): {tr_d}\n")
            fh.write(f"\nTop-level entries ({len(top)}): {', '.join(top[:LIST_MAX])}\n\n")
            fh.write(f"Files in tree: {len(paths) if snap.get('commit') else 'unknown; paths below are the dataset rows'}\n\n")
            fh.write(f"SKILL.md under a root agent directory such as .claude/skills/ ({len(root)}):\n")
            fh.write("".join(f"- {p}\n" for p in root[:LIST_MAX]) + ("- [...]\n" if len(root) > LIST_MAX else ""))
            fh.write(f"\nSKILL.md anywhere else ({len(other)}):\n")
            fh.write("".join(f"- {p}\n" for p in other[:LIST_MAX]) + ("- [...]\n" if len(other) > LIST_MAX else ""))
            fh.write(f"\nREADME (first {README_CHARS:,} characters after removing images, badges and HTML):\n\n")
            fh.write((readme or "(none)") + "\n")
            if tr_r:
                fh.write(f"\nREADME, machine translation ({lang_r} to English, DeepL):\n\n{tr_r}\n")
        print(f"{r.sid:4d} {lang_d}/{lang_r} {'T' if (tr_d or tr_r) else ' '} {source}", flush=True)

    pd.DataFrame(log).to_csv("data/private/validation/material_languages.csv", index=False)
    n = sum(x["translated_description"] or x["translated_readme"] for x in log)
    with open(SIDECAR, "w") as fh:
        json.dump({"service": "DeepL API", "target_lang": "EN-US", "model_type": "prefer_quality_optimized (README)",
                   "detector": "lingua, all languages, confidence >= 0.60", "date": dt.date.today().isoformat(),
                   "characters_sent": chars, "repositories_translated": int(n),
                   "note": "Aid for human coders only."}, fh, indent=2)
    print(f"\n{len(log)} material files written; {n} with a translation; {chars:,} characters sent to DeepL")


if __name__ == "__main__":
    main()
