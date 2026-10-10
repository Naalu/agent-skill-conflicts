"""Rebuild commit-history fields for the flagged skills (representative copies only), for the born-stale check.

Output: hist/part-NNNNN.parquet with file_sha, repo, first_commit_at, last_commit_at, commit_count, first_ai_coauthor.
Same row filter as the pilot's table `h`: history_fetched=1, dedup_primary=1, filename exactly SKILL.md.
"""
import duckdb, subprocess, sys, time, os
BASE = 'https://huggingface.co/datasets/mvaccargiu/gitskills/resolve/main/data/artifacts'
AI = r"(?i)co-authored-by:\s*[^\n]*(claude|copilot|codex|cursor|gemini|chatgpt|openai|devin|aider|amp\b|opencode|jules|windsurf|cline|kiro)"
con = duckdb.connect()
con.execute("SET threads=1; SET memory_limit='2GB'; SET preserve_insertion_order=false;")
con.execute("CREATE TABLE want AS SELECT DISTINCT file_sha FROM read_csv_auto('flagged_occurrences.csv')")
for i in range(int(sys.argv[1]), int(sys.argv[2])):
    out = f'hist/part-{i:05d}.parquet'
    if os.path.exists(out): continue
    t = time.time(); tmp = f'dlh-{i:05d}.parquet'
    subprocess.run(['curl', '-sS', '-L', '--fail', '--retry', '3', '-o', tmp, f'{BASE}/part-{i:05d}.parquet'], check=True)
    con.execute(f"""COPY (SELECT p.file_sha, p.repo_full_name AS repo, p.first_commit_at, p.last_commit_at, p.commit_count,
                                regexp_matches(coalesce(p.first_commit_message,''), '{AI}') AS first_ai_coauthor
                         FROM read_parquet('{tmp}') p SEMI JOIN want USING (file_sha)
                         WHERE p.history_fetched=1 AND p.dedup_primary=1 AND p.filename='SKILL.md')
                   TO '{out}.tmp' (FORMAT parquet, COMPRESSION zstd)""")
    os.replace(f'{out}.tmp', out); os.remove(tmp)
    print(i, round(time.time() - t, 1), 's', flush=True)
