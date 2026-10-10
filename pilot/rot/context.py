"""Context check for retired-model mentions.

For each skill naming a model retired by the snapshot, look at +/-90 characters around every such mention and
flag windows containing a warning cue (deprecated, do not use, replaced by ...). A skill is 'warning-only' when
every retired mention sits in such a window; otherwise at least one mention presents the model as usable.
Also writes label_sample.csv (200 random mentions) for two human coders.
"""
import duckdb, re, csv, random, datetime as dt, sys
sys.argv = ['curve.py']; import importlib.util
spec = importlib.util.spec_from_file_location('curve_helpers', 'resolve_only.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
MODEL = re.compile(r"claude-(?:[0-9]|opus|sonnet|haiku|instant)[a-z0-9.\-]*|gpt-[0-9][a-z0-9.\-]*|\bo[134]-(?:mini|pro|preview)\b|text-davinci-00[0-9]|code-davinci-00[0-9]"
                   r"|text-embedding-(?:ada-002|3-small|3-large)|dall-e-[23]|gemini-[0-9][a-z0-9.\-]*|gemini-pro(?:-vision)?\b|text-bison[a-z0-9@\-]*")
WARN = re.compile(r"do not use|don't use|dont use|never use|avoid|deprecat|retired|legacy|no longer|obsolete|outdated|sunset|shut ?down|discontinu|replaced by|"
                  r"instead of|migrat|formerly|previously|\bwas\b|\bold(er)?\b|\beol\b|end[- ]of[- ]life|弃用|棄用|已停|廃止|非推奨")
SNAP = dt.date(2026, 7, 31)
con = duckdb.connect('pilot.duckdb', read_only=True)
rows = con.execute("""SELECT f.file_sha, f.repo_full_name, f.path, f.content FROM read_parquet('flagged/*.parquet') f
                      JOIN rot2 USING (file_sha) WHERE rot2.first_ret <= DATE '2026-07-31'""").fetchall()
skills = usable = 0; mentions = []
for sha, repo, path, content in rows:
    lc = content.lower(); wins = []
    for m in MODEL.finditer(lc):
        d = R.resolve(m.group(0))
        if d and d <= SNAP:
            s, e = max(0, m.start() - 90), min(len(lc), m.end() + 90)
            wins.append((m.group(0), content[s:e].replace('\n', ' ⏎ '), bool(WARN.search(lc[s:e]))))
    if not wins: continue
    skills += 1; usable += any(not w for _, _, w in wins)
    mentions.append((sha, repo, path) + random.Random(sha).choice(wins))
print('skills re-checked:', skills, '| at least one retired mention without a warning cue: %.1f%%' % (100 * usable / skills))
print('share of sampled mentions inside a warning window: %.1f%%' % (100 * sum(m[5] for m in mentions) / len(mentions)))
random.Random(7).shuffle(mentions)
with open('label_sample.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['id','repo','path','model','context','heuristic_warning','coder1','coder2'])
    for i, (sha, repo, path, model, ctx, warn) in enumerate(mentions[:200], 1): w.writerow([i, repo, path, model, ctx, int(warn), '', ''])
for i, (sha, repo, path, model, ctx, warn) in enumerate(mentions[:60], 1):
    k = ctx.lower().find(model); print(f"{i:02d} {'W' if warn else '-'} | {ctx[max(0,k-60):k+len(model)+55]}")
