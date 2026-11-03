"""Scan every representative SKILL.md body once and keep the small per-hash flags the working-dataset rules need.

Implements the skill-level rules of the run-log entry "Working dataset v1" (2026-11-03). Downloads each artifacts
part from the Hugging Face mirror, computes the flags in DuckDB, deletes the download (same pattern as
pilot/collide/fm_scan.py). Output: data/interim/body_flags.parquet, one row per file_sha with
  instruction_lines   non-blank lines after the front matter
  meaningful_tokens   alphabetic tokens of three or more letters, minus a short stopword list
  placeholder         body contains TODO/FIXME, {{...}} template variables, <your-...> or "lorem ipsum",
                      and has fewer than 15 instruction lines
  dmi                 front matter sets disable-model-invocation: true
  skeleton            md5 of the ordered list of markdown headings (for the bulk/generated flag)
Usage: uv run python src/body_scan.py START END   (artifact part numbers, END exclusive; 0 31 for everything)
"""
import glob
import os
import subprocess
import sys
import time

import duckdb

BASE = "https://huggingface.co/datasets/mvaccargiu/gitskills/resolve/main/data"
OUT = "data/interim/body_flags"
STOP = "the|and|for|with|that|this|you|your|are|from|use|when|not|can|all|any|has|have|will|into|its|our|also|but|how|what|which|then"
os.makedirs(OUT, exist_ok=True)
con = duckdb.connect()
con.execute("SET threads=2; SET memory_limit='4GB'; SET preserve_insertion_order=false;")
for i in range(int(sys.argv[1]), int(sys.argv[2])):
    out = f"{OUT}/part-{i:05d}.parquet"
    if os.path.exists(out):
        continue
    t = time.time(); tmp = f"dl-{i:05d}.parquet"
    subprocess.run(["curl", "-sS", "-L", "--fail", "--retry", "3", "-o", tmp, f"{BASE}/artifacts/part-{i:05d}.parquet"], check=True)
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
