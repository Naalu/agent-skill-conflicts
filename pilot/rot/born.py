"""Born-stale check: first commit of the skill is later than the retirement date of a model it names."""
import duckdb, pandas as pd
con = duckdb.connect('pilot.duckdb')
con.execute("SET threads=1; SET memory_limit='2GB';")
RET = [  # (prefix, retirement date) -- vendor tables fetched 2026-10-06; gemini-1.x and text-bison from prior knowledge
 ('claude-1','2024-11-06'),('claude-instant','2024-11-06'),('claude-2','2025-07-21'),('claude-3-sonnet','2025-07-21'),
 ('claude-3-5-sonnet','2025-10-28'),('claude-3.5-sonnet','2025-10-28'),('claude-3-opus','2026-01-05'),
 ('claude-3-7-sonnet','2026-02-19'),('claude-3.7-sonnet','2026-02-19'),('claude-3-5-haiku','2026-02-19'),('claude-3.5-haiku','2026-02-19'),
 ('claude-3-haiku','2026-04-20'),('claude-sonnet-4-2025','2026-06-15'),('claude-opus-4-2025','2026-06-15'),
 ('claude-sonnet-4-0','2026-06-15'),('claude-opus-4-0','2026-06-15'),
 ('text-davinci-00','2024-01-04'),('gpt-4-vision-preview','2024-12-06'),('gpt-3.5-turbo-0613','2024-09-13'),('gpt-3.5-turbo-16k','2024-09-13'),
 ('gpt-4-32k','2025-06-06'),('gpt-4.5','2025-07-14'),('o1-preview','2025-07-28'),('o1-mini','2025-10-27'),
 ('gpt-4o-latest','2026-02-17'),('gpt-4-0314','2026-03-26'),('gpt-4-1106','2026-03-26'),('gpt-4-0125-preview','2026-03-26'),('gpt-4-turbo-preview','2026-03-26'),
 ('gpt-4o-realtime-preview','2026-05-07'),('gpt-4o-audio-preview','2026-05-07'),
 ('gpt-5-codex','2026-07-23'),('gpt-5.1-codex','2026-07-23'),('gpt-5.2-codex','2026-07-23'),('gpt-5-chat-latest','2026-07-23'),('gpt-5.1-chat-latest','2026-07-23'),
 ('gemini-1.','2025-09-24'),('gemini-pro','2025-02-15'),('gemini-2.0-flash-lite-preview','2025-12-09'),('gemini-2.0','2026-06-01'),
 ('gemini-2.5-pro-preview','2025-12-02'),('gemini-2.5-flash-preview','2026-02-17'),('gemini-2.5-flash-lite-preview','2026-03-31'),
 ('gemini-3-pro-preview','2026-03-09'),('gemini-3.1-flash-lite-preview','2026-05-25')]
EXACT = {'claude-sonnet-4':'2026-06-15','claude-opus-4':'2026-06-15'}
def earliest_ret(ms):
    best = None
    for m in ms.split('|'):
        m = m.strip().rstrip('.-'); d = EXACT.get(m)
        if d is None:
            for p, dd in RET:
                if m.startswith(p): d = dd; break
        if d and (best is None or d < best): best = d
    return best
df = con.execute("""SELECT h.file_sha, cf.models, h.first_at, h.commits, h.first_ai FROM h JOIN cf USING (file_sha)
                    JOIN rot USING (file_sha) WHERE rot.any_expired AND h.first_at >= '2025-10-01'""").fetchdf()
df['ret'] = df.models.map(earliest_ret)
df = df[df.ret.notna()]
df['born_stale'] = df.first_at.str[:10] > df.ret
print('dated skills naming a model retired by the snapshot (with a mapped date):', len(df))
print('  born stale (first commit after retirement): %d = %.1f%%' % (df.born_stale.sum(), 100*df.born_stale.mean()))
s = df[df.commits == 1]
print('  single-commit only: n=%d, born stale %.1f%%' % (len(s), 100*s.born_stale.mean()))
print('  by AI co-author on first commit:'); print(df.groupby('first_ai').born_stale.agg(['size','mean']).round(3).to_string())
