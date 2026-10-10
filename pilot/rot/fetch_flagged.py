"""Rebuild the text of flagged skills (those naming a model retired by 2026-07-31) from the Hugging Face mirror.

Input : flagged_occurrences.csv (repo, path, file_sha, first_ret) written by the pilot under the corrected definition.
Output: flagged/part-NNNNN.parquet with file_sha and content, one row per distinct content.
Each artifacts file is downloaded with curl (which honours the session proxy), filtered locally, then deleted.
"""
import duckdb, subprocess, sys, time, os
BASE = 'https://huggingface.co/datasets/mvaccargiu/gitskills/resolve/main/data/artifacts'
con = duckdb.connect()
con.execute("SET threads=1; SET memory_limit='2GB'; SET preserve_insertion_order=false;")
con.execute("CREATE TABLE want AS SELECT DISTINCT file_sha FROM read_csv_auto('flagged_occurrences.csv')")
print('distinct contents wanted:', con.execute('SELECT count(*) FROM want').fetchone()[0], flush=True)
start, end = int(sys.argv[1]), int(sys.argv[2])
for i in range(start, end):
    out = f'flagged/part-{i:05d}.parquet'
    if os.path.exists(out): continue
    t = time.time(); tmp = f'dl-{i:05d}.parquet'
    subprocess.run(['curl', '-sS', '-L', '--fail', '--retry', '3', '-o', tmp, f'{BASE}/part-{i:05d}.parquet'], check=True)
    con.execute(f"""COPY (SELECT p.file_sha, any_value(p.content) AS content
                         FROM read_parquet('{tmp}') p SEMI JOIN want USING (file_sha)
                         WHERE p.content IS NOT NULL GROUP BY 1)
                   TO '{out}.tmp' (FORMAT parquet, COMPRESSION zstd)""")
    os.replace(f'{out}.tmp', out); os.remove(tmp)
    n = con.execute(f"SELECT count(*) FROM read_parquet('{out}')").fetchone()[0]
    print(i, n, 'rows', round(time.time() - t, 1), 's', flush=True)
