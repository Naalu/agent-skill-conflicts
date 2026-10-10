"""Classify model identifiers found in skills against vendor retirement dates.

Sources (fetched 2026-10-06, saved in expiry/): Anthropic model-deprecations, OpenAI deprecations,
Google Gemini deprecations. Cut-off for 'expired at snapshot' = 2026-07-31.
gemini-1.x is classed as expired from prior knowledge; it is no longer listed on the current page.
"""
import duckdb, re, collections
con = duckdb.connect('pilot.duckdb')
con.execute("SET threads=1; SET memory_limit='2GB';")
con.execute("CREATE OR REPLACE TABLE cf AS SELECT * FROM read_parquet('cflags/*.parquet')")

EXP_PREFIX = [  # retired on or before 2026-07-31
 'claude-1', 'claude-2', 'claude-instant', 'claude-3-', 'claude-3.', 'claude-sonnet-4-2025', 'claude-opus-4-2025',
 'claude-sonnet-4-0', 'claude-opus-4-0',
 'text-davinci-00', 'code-davinci-00', 'gpt-4-32k', 'gpt-4-0314', 'gpt-4-1106', 'gpt-4-0125-preview', 'gpt-4-turbo-preview',
 'gpt-4-vision-preview', 'gpt-4.5', 'o1-preview', 'o1-mini', 'gpt-3.5-turbo-0301', 'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-16k',
 'gpt-4o-realtime-preview', 'gpt-4o-audio-preview', 'gpt-4o-mini-realtime-preview', 'gpt-4o-mini-audio-preview',
 'gpt-4o-search-preview', 'gpt-4o-mini-search-preview', 'gpt-4o-latest',
 'gpt-5-codex', 'gpt-5.1-codex', 'gpt-5.2-codex', 'gpt-5-chat-latest', 'gpt-5.1-chat-latest',
 'gemini-1.', 'gemini-pro', 'gemini-2.0', 'gemini-2.5-pro-preview', 'gemini-2.5-flash-preview', 'gemini-2.5-flash-lite-preview',
 'gemini-3-pro-preview', 'gemini-3.1-flash-lite-preview', 'text-bison']
EXP_EXACT = {'claude-sonnet-4', 'claude-opus-4', 'claude-3'}
SOON_EXACT = {  # shut down between 2026-08-01 and 2026-10-23 (after the snapshot)
 'gpt-4', 'gpt-4-0613', 'gpt-4-turbo', 'gpt-4-turbo-2024-04-09', 'gpt-3.5-turbo', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-instruct',
 'o1-pro', 'o3-mini', 'o4-mini', 'gpt-4o-2024-05-13', 'gpt-4.1-nano', 'claude-opus-4-1', 'claude-opus-4-1-20250805',
 'gpt-5.2-chat-latest', 'gpt-5.3-chat-latest'}

def norm(m): return m.strip().rstrip('.-')
def status(m):
    m = norm(m)
    if m in EXP_EXACT or any(m.startswith(p) for p in EXP_PREFIX): return 'expired'
    if m in SOON_EXACT: return 'soon'
    return 'other'

rows = con.execute("SELECT file_sha, models FROM cf WHERE models <> ''").fetchall()
out, cnt = [], collections.Counter()
for sha, ms in rows:
    ids = {norm(x) for x in ms.split('|') if norm(x)}
    st = {status(x) for x in ids}
    out.append((sha, len(ids), 'expired' in st, 'soon' in st, all(status(x) == 'expired' for x in ids)))
    cnt.update(ids)
con.execute("CREATE OR REPLACE TABLE rot (file_sha VARCHAR, n_models INT, any_expired BOOL, any_soon BOOL, all_expired BOOL)")
con.executemany("INSERT INTO rot VALUES (?,?,?,?,?)", out) if len(out) < 5000 else None
import pandas as pd
if len(out) >= 5000:
    df = pd.DataFrame(out, columns=['file_sha','n_models','any_expired','any_soon','all_expired'])
    con.execute("INSERT INTO rot SELECT * FROM df")
print('skills naming a model:', len(out))
print('top 40 identifiers:'); 
for k, v in cnt.most_common(40): print(f'  {v:7d}  {status(k):8s} {k}')
