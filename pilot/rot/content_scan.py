"""Scan the `content` column of each artifacts file and keep only small derived flags.

Output: one row per distinct content (dedup_primary=1 rows carrying text).
  h2sig   : first 15 level-2 headings, lowercased, '|'-joined (template fingerprint)
  models  : distinct vendor model identifiers mentioned (Anthropic / OpenAI / Google)
  pyver   : distinct Python minor versions mentioned
  nodever : distinct Node.js major versions mentioned
  actions : distinct GitHub Actions pins of the form actions/<name>@v<N>
"""
import duckdb, sys, time
BASE = 'https://huggingface.co/datasets/mvaccargiu/gitskills/resolve/main/data'
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; SET threads=1; SET memory_limit='2GB'; SET preserve_insertion_order=false;")
MODEL = (r"claude-(?:[0-9]|opus|sonnet|haiku|instant)[a-z0-9.\-]*"
         r"|gpt-[0-9][a-z0-9.\-]*|\bo[134]-(?:mini|pro|preview)\b|text-davinci-00[0-9]|code-davinci-00[0-9]"
         r"|text-embedding-(?:ada-002|3-small|3-large)|dall-e-[23]"
         r"|gemini-[0-9][a-z0-9.\-]*|gemini-pro(?:-vision)?\b|text-bison[a-z0-9@\-]*")
PY = r"python[ ]?(?:>=|==|~=|@|:|-)?[ ]?(3\.[0-9]{1,2})\b"
NODE = r"(?:node(?:\.js|js)?[ ]?(?:>=|@|:|-)?[ ]?v?|node-version:[ ]?['\"]?|nvm (?:use|install) v?)([0-9]{2})(?:\.[0-9x]+)*\b"
ACT = r"actions/[a-z\-]+@v[0-9]+"
start, end = int(sys.argv[1]), int(sys.argv[2])
for i in range(start, end):
    t = time.time()
    src = f"{BASE}/artifacts/part-{i:05d}.parquet"
    con.execute(f"""
    COPY (
      WITH s AS (SELECT file_sha, content, lower(content) AS lc FROM read_parquet('{src}')
                 WHERE content IS NOT NULL AND dedup_primary=1)
      SELECT file_sha,
             length(content) AS n_chars,
             length(content) - length(replace(content, chr(10), '')) + 1 AS n_lines,
             array_to_string(list_slice(regexp_extract_all(lc, '(?m)^##[ \\t]+([^\\n]{{1,80}})', 1), 1, 15), '|') AS h2sig,
             array_to_string(list_sort(list_distinct(regexp_extract_all(lc, '{MODEL}'))), '|') AS models,
             array_to_string(list_sort(list_distinct(regexp_extract_all(lc, '{PY}', 1))), '|') AS pyver,
             array_to_string(list_sort(list_distinct(regexp_extract_all(lc, $${NODE}$$, 1))), '|') AS nodever,
             array_to_string(list_sort(list_distinct(regexp_extract_all(lc, '{ACT}'))), '|') AS actions
      FROM s
    ) TO 'cflags/part-{i:05d}.parquet' (FORMAT parquet, COMPRESSION zstd)
    """)
    print(i, round(time.time()-t, 1), 's', flush=True)
