"""Resolver only (shared helper). Resolve each model mention to a retirement date and compute the expiry curve over calendar time.

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
