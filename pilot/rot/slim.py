"""Materialise a slim local copy of `artifacts` (no content column).

One row per SKILL.md occurrence. Adds an AI-co-author flag derived from the
first commit message so the large message columns need not be stored.
"""
import duckdb, sys, time
BASE = 'https://huggingface.co/datasets/mvaccargiu/gitskills/resolve/main/data'
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; SET threads=1; SET memory_limit='2GB'; SET preserve_insertion_order=false;")
AI = r"(?i)co-authored-by:\s*[^\n]*(claude|copilot|codex|cursor|gemini|chatgpt|openai|devin|aider|amp\b|opencode|jules|windsurf|cline|kiro)"
start, end = int(sys.argv[1]), int(sys.argv[2])
for i in range(start, end):
    t = time.time()
    src = f"{BASE}/artifacts/part-{i:05d}.parquet"
    con.execute(f"""
    COPY (
      SELECT repo_full_name, path, filename, location_class, file_sha,
             content_fetched, frontmatter_valid, name, description, body_chars,
             history_fetched, dedup_primary, first_commit_at, last_commit_at,
             commit_count, sibling_count, has_scripts, has_references,
             first_commit_author, first_commit_author_type, last_commit_author_type,
             regexp_matches(coalesce(first_commit_message,''), '{AI}') AS first_ai_coauthor,
             regexp_matches(coalesce(last_commit_message,''),  '{AI}') AS last_ai_coauthor
      FROM read_parquet('{src}')
    ) TO 'slim/part-{i:05d}.parquet' (FORMAT parquet, COMPRESSION zstd)
    """)
    print(i, round(time.time()-t, 1), 's', flush=True)
