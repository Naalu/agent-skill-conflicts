"""Rebuild a slim local copy of `artifacts` (no content column) from the Hugging Face Parquet mirror.

One row per SKILL.md occurrence: repository, path, filename, content hash, front-matter flag, name, description,
representative flag and commit-history fields. Each source file is downloaded with curl, reduced, then deleted.
Also downloads the `repos` table (repository metadata).
Usage: python slim_local.py START END      (artifact part numbers, END exclusive; 0 31 for everything)
"""
import duckdb, os, subprocess, sys, time
BASE = 'https://huggingface.co/datasets/mvaccargiu/gitskills/resolve/main/data'
con = duckdb.connect()
con.execute("SET threads=2; SET memory_limit='4GB'; SET preserve_insertion_order=false;")
if not os.path.exists('repos.parquet'):
    subprocess.run(['curl', '-sS', '-L', '--fail', '--retry', '3', '-o', 'repos.parquet', f'{BASE}/repos/part-00000.parquet'], check=True)
for i in range(int(sys.argv[1]), int(sys.argv[2])):
    out = f'slim/part-{i:05d}.parquet'
    if os.path.exists(out):
        continue
    t = time.time(); tmp = f'dl-{i:05d}.parquet'
    subprocess.run(['curl', '-sS', '-L', '--fail', '--retry', '3', '-o', tmp, f'{BASE}/artifacts/part-{i:05d}.parquet'], check=True)
    con.execute(f"""COPY (SELECT repo_full_name, path, filename, location_class, file_sha, content_fetched, frontmatter_valid,
                                name, description, body_chars, history_fetched, dedup_primary, first_commit_at, last_commit_at,
                                commit_count, has_scripts, has_references
                         FROM read_parquet('{tmp}'))
                   TO '{out}.tmp' (FORMAT parquet, COMPRESSION zstd)""")
    os.replace(f'{out}.tmp', out); os.remove(tmp)
    print(i, round(time.time() - t, 1), 's', flush=True)
print('done', flush=True)
