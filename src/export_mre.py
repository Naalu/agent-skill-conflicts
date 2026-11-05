"""Assemble the coverage-gap package for the dataset authors (mre/ folder; not committed, it names repositories).

Reads data/private/validation/{sample,copy_check,twin_verdicts}.csv and data/interim/slim/*.parquet. Writes
  mre/examples.csv                 the repositories with dropped twins: counts from the check
  mre/dataset_rows/<owner>__<repo>.csv   the dataset's rows for each (repo_full_name, path, file_sha, location_class)
Then copy the scripts from the package folder in beside them and zip the lot. Usage: uv run python src/export_mre.py
"""
import os

import duckdb
import pandas as pd

c = pd.read_csv("data/private/validation/copy_check.csv")
s = pd.read_csv("data/private/validation/sample.csv")
v = pd.read_csv("data/private/validation/twin_verdicts.csv")
ex = c[c.dropped_twin > 0].merge(s[["sid", "n_dirs", "n_names"]], on="sid")
real = v[v.existed_in_july.fillna(False).astype(bool)].groupby("sid").size().rename("twins_existing_before_snapshot")
ex = ex.merge(real, on="sid", how="left").fillna({"twins_existing_before_snapshot": 0})
os.makedirs("mre/dataset_rows", exist_ok=True)
ex[["repo", "n_dirs", "dataset_root_skills", "gh_root_skills", "missing_from_dataset", "dropped_twin",
    "twins_existing_before_snapshot", "new_content", "edited_since"]].rename(columns={
    "dataset_root_skills": "root_skills_in_dataset", "gh_root_skills": "root_skills_on_github_now",
    "dropped_twin": "missing_with_sha_known_in_repo"}).sort_values("repo").to_csv("mre/examples.csv", index=False)
con = duckdb.connect()
repos = ",".join(f"'{r}'" for r in ex.repo)
rows = con.execute(f"""SELECT repo_full_name, path, file_sha, location_class FROM read_parquet('data/interim/slim/*.parquet')
                       WHERE repo_full_name IN ({repos}) ORDER BY 1, 2""").fetchdf()
for repo, g in rows.groupby("repo_full_name"):
    g.to_csv(f"mre/dataset_rows/{repo.replace('/', '__')}.csv", index=False)
print(f"{len(ex)} repositories in mre/examples.csv; {len(rows)} dataset rows written under mre/dataset_rows/")
