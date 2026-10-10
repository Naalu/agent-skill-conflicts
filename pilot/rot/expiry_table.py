"""Build one identifier -> retirement-date table from the three vendor deprecation pages saved in expiry/.

Output: expiry/retirements.csv with columns vendor, model, retire_date (ISO), basis.
basis = 'vendor table' for rows parsed from the pages; 'prior knowledge' for families no longer listed.
"""
import re, csv, datetime as dt
MONTHS = {m: i for i, m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'], 1)}
def parse_date(s):
    s = s.replace('\u2011', '-').strip()
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m: return dt.date(int(m[1]), int(m[2]), int(m[3]))
    m = re.search(r'([A-Za-z]{3})[a-z]*\.? (\d{1,2}), (\d{4})', s)
    if m and m[1].lower() in MONTHS: return dt.date(int(m[3]), MONTHS[m[1].lower()], int(m[2]))
    return None
def cells(line): return [c.strip() for c in re.split(r'(?<!\\)\|', line.strip().strip('|'))]
rows = {}
def add(vendor, model, d, basis='vendor table'):
    model = model.lower().strip()
    if d and (model not in rows or d < rows[model][1]): rows[model] = (vendor, d, basis)
for line in open('expiry/anthropic.md'):
    if not line.startswith('|'): continue
    c = cells(line)
    if len(c) == 3 and '`' in c[1]:
        for m in re.findall(r'`([^`]+)`', c[1]): add('anthropic', m, parse_date(c[0]))
    if len(c) == 4 and c[1] in ('Retired', 'Deprecated') and 'Not sooner' not in c[3]: add('anthropic', c[0], parse_date(c[3]))
for line in open('expiry/openai.md'):
    if not line.startswith('|'): continue
    c = cells(line)
    if len(c) >= 3 and '`' in c[1] and 'fine-tuning' not in c[1]:
        d = parse_date(c[0])
        for m in re.findall(r'`([^`]+)`', c[1]): add('openai', m, d)
for line in open('expiry/google.md'):
    if not line.startswith('|'): continue
    c = cells(line)
    if len(c) >= 3 and c[0].startswith('`'):
        for m in re.findall(r'`([^`]+)`', c[0]): add('google', m, parse_date(c[2]))
for model, d in [('gemini-1.5-pro','2025-09-24'),('gemini-1.5-flash','2025-09-24'),('gemini-1.0-pro','2025-02-15'),('gemini-pro','2025-02-15'),
                 ('gemini-pro-vision','2025-02-15'),('text-bison','2025-04-09')]:
    if model not in rows: add('google', model, dt.date.fromisoformat(d), 'prior knowledge')
with open('expiry/retirements.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['vendor','model','retire_date','basis'])
    for m, (v, d, b) in sorted(rows.items(), key=lambda kv: (kv[1][0], kv[1][1])): w.writerow([v, m, d.isoformat(), b])
import collections
print(len(rows), 'identifiers;', collections.Counter(v for v, _, _ in rows.values()))
print('retired by 2026-07-31:', sum(d <= dt.date(2026,7,31) for _, d, _ in rows.values()), '| by 2027-04-27:', sum(d <= dt.date(2027,4,27) for _, d, _ in rows.values()))
