"""Resolve each model mention to a retirement date and compute the expiry curve over calendar time.

Writes table `rot2` (per skill: earliest and latest retirement date among named models) and expiry_curve.csv.
Future points use dates the vendors have already announced, so they are lower bounds.
"""
import duckdb, re, csv, datetime as dt, collections, pandas as pd
TAB = {r['model']: dt.date.fromisoformat(r['retire_date']) for r in csv.DictReader(open('expiry/retirements.csv'))}
TAB['gpt-4o-latest'] = TAB.get('chatgpt-4o-latest', dt.date(2026, 2, 17))   # regex captures the tail of chatgpt-4o-latest
FAMILY = [('claude-instant','2024-11-06'),('claude-1','2024-11-06'),('claude-2','2025-07-21'),('claude-3-5-sonnet','2025-10-28'),
          ('claude-3-7-sonnet','2026-02-19'),('claude-3-5-haiku','2026-02-19'),('claude-3-opus','2026-01-05'),('claude-3-haiku','2026-04-20'),
          ('claude-3-sonnet','2025-07-21'),('claude-3','2026-04-20'),('gemini-1.','2025-09-24'),('gemini-2.0','2026-06-01'),
          ('gemini-pro','2025-02-15'),('text-davinci','2024-01-04'),('code-davinci','2024-01-04'),('gpt-4-32k','2025-06-06'),
          ('gpt-3.5-turbo-16k','2024-09-13'),('gpt-3.5-turbo-0613','2024-09-13'),('gpt-3.5-turbo-0301','2024-09-13'),
          ('gpt-4.5','2025-07-14'),('text-bison','2025-04-09')]
SUFFIX = re.compile(r'^(-(\d{2,8}|preview|exp|experimental|latest|00\d|v\d))+$')
KEYS = sorted(TAB, key=len, reverse=True)
def norm(m):
    m = m.strip().lower().rstrip('.-')
    if m.startswith('claude-') and not re.match(r'claude-(1|2|instant)', m): m = m.replace('.', '-')
    m = re.sub(r'-latest$', '', m)
    if m.startswith('claude-'): m = re.sub(r'-0$', '', m)
    return m
def resolve(m):
    m = norm(m)
    if m in TAB: return TAB[m]
    for t in KEYS:
        if m.startswith(t) and SUFFIX.match(m[len(t):]): return TAB[t]
    snaps = [d for t, d in TAB.items() if re.fullmatch(re.escape(m) + r'-\d{8}', t)]
    if snaps: return max(snaps)
    for p, d in FAMILY:
        if m.startswith(p): return dt.date.fromisoformat(d)
    return None
con = duckdb.connect('pilot.duckdb')
con.execute("SET threads=1; SET memory_limit='2GB';")
rows = con.execute("SELECT cf.file_sha, cf.models FROM cf JOIN v USING (file_sha) WHERE cf.models <> ''").fetchall()
out, unresolved = [], collections.Counter()
for sha, ms in rows:
    ids = {norm(x) for x in ms.split('|') if norm(x)}
    ds = {i: resolve(i) for i in ids}
    for i, d in ds.items():
        if d is None: unresolved[i] += 1
    dated = [d for d in ds.values() if d]
    out.append((sha, len(ids), min(dated) if dated else None, max(dated) if dated and len(dated) == len(ids) else None))
df = pd.DataFrame(out, columns=['file_sha','n_models','first_ret','all_ret'])
con.execute("CREATE OR REPLACE TABLE rot2 AS SELECT * FROM df")
n = len(df)
occ = con.execute("SELECT o.file_sha, count(*) c FROM o JOIN rot2 USING (file_sha) WHERE o.f_valid GROUP BY 1").fetchdf().set_index('file_sha').c
df['occ'] = df.file_sha.map(occ).fillna(1)
pts = [dt.date(2025,10,31), dt.date(2026,1,31), dt.date(2026,4,30), dt.date(2026,7,31), dt.date(2026,10,7), dt.date(2026,10,31),
       dt.date(2026,12,23), dt.date(2027,1,31), dt.date(2027,4,26)]
print('skills naming a model (valid, distinct):', n)
with open('expiry_curve.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['date','pct_any_named_model_retired','pct_all_named_models_retired','pct_occurrence_weighted_any'])
    d = dt.date(2025, 10, 31); grid = []
    while d <= dt.date(2027, 4, 30):
        grid.append(d); nxt = (d.replace(day=1) + dt.timedelta(days=62)).replace(day=1) - dt.timedelta(days=1); d = nxt
    for d in sorted(set(grid + pts)):
        a = 100 * (df.first_ret.notna() & (df.first_ret <= d)).mean()
        b = 100 * (df.all_ret.notna() & (df.all_ret <= d)).mean()
        c = 100 * (df.occ[(df.first_ret.notna() & (df.first_ret <= d))].sum() / df.occ.sum())
        w.writerow([d.isoformat(), round(a, 2), round(b, 2), round(c, 2)])
        if d in pts: print(f'  {d}: any retired {a:5.1f}%   all retired {b:5.1f}%   occurrence-weighted any {c:5.1f}%')
print('top unresolved identifiers (treated as alive):', unresolved.most_common(14))
