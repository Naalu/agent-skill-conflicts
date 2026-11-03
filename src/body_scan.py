"""Download each artifacts part once and keep two small derived files; delete the download.

1. data/interim/slim/part-NNNNN.parquet: every occurrence, without the content column (the same columns as
   pilot/collide/slim_local.py kept), about 300 MB in total. This is what src/build_working_set.py reads.
2. data/interim/body_flags/part-NNNNN.parquet: per-hash body flags for the skill-level rules of the run-log entry
   "Working dataset v1" (2026-11-03), merged into data/interim/body_flags.parquet after the last part:
  instruction_lines   non-blank lines after the front matter
  meaningful_tokens   alphabetic tokens of three or more letters, minus a short stopword list
  placeholder         body contains TODO/FIXME, {{...}} template variables, <your-...> or "lorem ipsum",
                      and has fewer than 15 instruction lines
  dmi                 front matter sets disable-model-invocation: true
  skeleton            md5 of the ordered list of markdown headings (for the bulk/generated flag)
Also downloads the repos table to data/interim/repos.parquet if it is not there.
Usage: uv run python src/body_scan.py START END   (artifact part numbers, END exclusive; 0 31 for everything)
About 6 GB over the wire for all 31 parts; nothing large is kept. Safe to re-run; finished parts are skipped.
"""
import glob
import os
import subprocess
import sys
import time

import duckdb

BASE = "https://huggingface.co/datasets/mvaccargiu/gitskills/resolve/main/data"
OUT = "data/interim/body_flags"
SLIM = "data/interim/slim"
REPOS = "data/interim/repos.parquet"
STOP = "the|and|for|with|that|this|you|your|are|from|use|when|not|can|all|any|has|have|will|into|its|our|also|but|how|what|which|then"
os.makedirs(OUT, exist_ok=True); os.makedirs(SLIM, exist_ok=True)
con = duckdb.connect()
con.execute("SET threads=2; SET memory_limit='4GB'; SET preserve_insertion_order=false;")
def readable(path: str) -> bool:
    try:
        con.execute(f"SELECT count(*) FROM read_parquet('{path}')").fetchone()
        return True
    except duckdb.Error:
        return False


for attempt in range(4):
    if os.path.exists(REPOS) and readable(REPOS):
        break
    if os.path.exists(REPOS):
        print("repos.parquet unreadable, downloading again", flush=True)
        os.remove(REPOS)
    subprocess.run(["curl", "-sS", "-L", "--fail", "--retry", "3", "-o", REPOS, f"{BASE}/repos/part-00000.parquet"], check=True)
    print("repos.parquet downloaded", flush=True)
else:
    sys.exit("repos.parquet: gave up after 4 downloads")
for i in range(int(sys.argv[1]), int(sys.argv[2])):
    out = f"{OUT}/part-{i:05d}.parquet"
    slim = f"{SLIM}/part-{i:05d}.parquet"
    if os.path.exists(out) and os.path.exists(slim):
        continue
    t = time.time(); tmp = f"dl-{i:05d}.parquet"
    for attempt in range(4):  # a truncated download fails to decompress; fetch it again rather than stop
        if os.path.exists(tmp):
            os.remove(tmp)
        subprocess.run(["curl", "-sS", "-L", "--fail", "--retry", "3", "-o", tmp, f"{BASE}/artifacts/part-{i:05d}.parquet"], check=True)
        if readable(tmp):
            break
        print(f"part {i}: download unreadable, attempt {attempt + 1} of 4", flush=True)
    else:
        sys.exit(f"part {i}: gave up after 4 downloads")
    if not os.path.exists(slim):
        con.execute(f"""COPY (SELECT repo_full_name, path, filename, location_class, file_sha, content_fetched,
                                    frontmatter_valid, name, description, body_chars, history_fetched, dedup_primary,
                                    first_commit_at, last_commit_at, commit_count, has_scripts, has_references
                             FROM read_parquet('{tmp}'))
                       TO '{slim}.tmp' (FORMAT parquet, COMPRESSION zstd)""")
        os.replace(f"{slim}.tmp", slim)
    con.execute(rf"""COPY (
      WITH s AS (
        SELECT file_sha,
               lower(regexp_extract(content, '(?s)\A\s*---[ \t]*\r?\n(.*?)\r?\n---', 1)) AS fm,
               regexp_replace(content, '(?s)\A\s*---[ \t]*\r?\n.*?\r?\n---[ \t]*\r?\n?', '') AS body
        FROM read_parquet('{tmp}') WHERE content IS NOT NULL AND dedup_primary = 1),
      m AS (
        SELECT file_sha, fm, body,
               len(list_filter(string_split(body, chr(10)), x -> trim(x) <> '')) AS instruction_lines,
               len(list_filter(regexp_extract_all(lower(body), '[a-z]{{3,}}'), x -> NOT regexp_matches(x, '^({STOP})$'))) AS meaningful_tokens
        FROM s)
      SELECT file_sha, instruction_lines, meaningful_tokens,
             (regexp_matches(body, '(?i)\bTODO\b|\bFIXME\b|\{{\{{[^}}]*\}}\}}|<your[-_ ]|lorem ipsum') AND instruction_lines < 15) AS placeholder,
             regexp_matches(fm, '(?m)^disable-model-invocation:\s*[''"]?true') AS dmi,
             md5(array_to_string(regexp_extract_all(body, '(?m)^#{{1,6}}[ \t]+(.+?)[ \t]*$', 1), '|')) AS skeleton
      FROM m) TO '{out}.tmp' (FORMAT parquet, COMPRESSION zstd)""")
    os.replace(f"{out}.tmp", out); os.remove(tmp)
    print(i, round(time.time() - t, 1), "s", flush=True)
parts = sorted(glob.glob(f"{OUT}/part-*.parquet"))
if len(parts) == 31:
    con.execute(f"COPY (SELECT * FROM read_parquet('{OUT}/*.parquet')) TO 'data/interim/body_flags.parquet' (FORMAT parquet, COMPRESSION zstd)")
    print("merged -> data/interim/body_flags.parquet")
print("done", flush=True)
