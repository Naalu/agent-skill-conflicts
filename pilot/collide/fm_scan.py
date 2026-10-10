"""Run 5 / P3: flag invocation-related front-matter fields for every representative SKILL.md copy.
Downloads each artifacts file, keeps one row per file_sha with small flags, deletes the download.
Usage: python fm_scan.py START END"""
import duckdb, os, subprocess, sys, time
BASE = 'https://huggingface.co/datasets/mvaccargiu/gitskills/resolve/main/data'
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='4GB'; SET preserve_insertion_order=false;")
for i in range(int(sys.argv[1]), int(sys.argv[2])):
    out = f'fm/part-{i:05d}.parquet'
    if os.path.exists(out): continue
    t = time.time(); tmp = f'dl-{i:05d}.parquet'
    subprocess.run(['curl', '-sS', '-L', '--fail', '--retry', '3', '-o', tmp, f'{BASE}/artifacts/part-{i:05d}.parquet'], check=True)
    con.execute(rf"""COPY (
      WITH s AS (SELECT file_sha, lower(regexp_extract(content, '(?s)\A\s*---[ \t]*\r?\n(.*?)\r?\n---', 1)) AS f
                 FROM read_parquet('{tmp}') WHERE content IS NOT NULL AND dedup_primary=1)
      SELECT file_sha, length(f) AS fm_chars,
             regexp_matches(f, '(?m)^disable-model-invocation:\s*[''"]?true') AS dmi,
             regexp_matches(f, '(?m)^user-invocable:\s*[''"]?false') AS not_user_invocable,
             regexp_matches(f, '(?m)^paths:') AS has_paths,
             regexp_matches(f, '(?m)^when_to_use:') AS has_wtu,
             regexp_matches(f, '(?m)^allowed-tools:') AS has_allowed_tools
      FROM s) TO '{out}.tmp' (FORMAT parquet, COMPRESSION zstd)""")
    os.replace(f'{out}.tmp', out); os.remove(tmp); print(i, round(time.time() - t, 1), 's', flush=True)
print('done', flush=True)
