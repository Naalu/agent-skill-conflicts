"""Redraw the hand-labelling sample under the corrected definition (2026-10-08).

Sampling frame : flagged_occurrences.csv, restricted to occurrences whose text names a model retired BEFORE the
                 dataset was collected. The mining runs ran 2026-07-09 to 2026-07-20, so the cut-off is 2026-07-08.
                 (The pilot used 2026-07-31, which wrongly admitted 17 OpenAI models retired on 2026-07-23.)
                 The bare family token 'claude-3' does not count. 32,261 occurrences, 7,804 repositories.
Design         : simple random sample of N repositories (fixed seed); within a repository one occurrence at random;
                 within that skill one retired-model mention at random. One mention per repository, so no single
                 repository can dominate the sample.
Shown to coders: repository, path, the model string, its retirement date, and +/-PAD characters of context.
                 No heuristic label is shown, so coders are not anchored. Each coder fills a separate copy.
Outputs        : label_sample.csv (UTF-8 with BOM so Excel opens it cleanly) and a console summary.
Usage          : python redraw_sample.py [N] [SEED]
"""
import collections, csv, datetime as dt, importlib.util, random, re, sys
import duckdb

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 20261008
PAD = 150
SNAPSHOT = dt.date(2026, 7, 8)     # day before the first mining run started
MODEL = re.compile(r"claude-(?:[0-9]|opus|sonnet|haiku|instant)[a-z0-9.\-]*|gpt-[0-9][a-z0-9.\-]*|\bo[134]-(?:mini|pro|preview)\b"
                   r"|text-davinci-00[0-9]|code-davinci-00[0-9]|text-embedding-(?:ada-002|3-small|3-large)|dall-e-[23]"
                   r"|gemini-[0-9][a-z0-9.\-]*|gemini-pro(?:-vision)?\b|text-bison[a-z0-9@\-]*")

spec = importlib.util.spec_from_file_location('resolver', 'resolve_only.py')
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)


def retired_mentions(content):
    """Return [(model string, retirement date, context)] for every retired-model mention in one skill."""
    lc, out = content.lower(), []
    for m in MODEL.finditer(lc):
        ident = R.norm(m.group(0))
        if ident == 'claude-3':
            continue
        d = R.resolve(ident)
        if d and d <= SNAPSHOT:
            s, e = max(0, m.start() - PAD), min(len(content), m.end() + PAD)
            ctx = content[s:m.start()] + '[[' + content[m.start():m.end()] + ']]' + content[m.end():e]
            out.append((m.group(0), d.isoformat(), ctx.replace('\r', '').replace('\n', ' ⏎ ')))
    return out


def main():
    con = duckdb.connect()
    text = dict(con.execute("SELECT file_sha, content FROM read_parquet('flagged/*.parquet')").fetchall())
    occ = collections.defaultdict(list)
    with open('flagged_occurrences.csv', newline='') as f:
        for r in csv.DictReader(f):
            if dt.date.fromisoformat(r['first_ret']) <= SNAPSHOT:
                occ[r['repo']].append((r['path'], r['file_sha']))
    repos = sorted(occ)
    rng = random.Random(SEED)
    order = rng.sample(repos, len(repos))            # a random permutation; take repositories in this order
    rows, skipped = [], 0
    for repo in order:
        if len(rows) == N:
            break
        path, sha = rng.choice(sorted(occ[repo]))
        ms = retired_mentions(text.get(sha, ''))
        if not ms:                                    # text missing or Python/DuckDB regex disagreement
            skipped += 1
            continue
        model, d, ctx = rng.choice(ms)
        rows.append((repo, path, sha, model, d, ctx))
    with open('label_sample.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['id', 'repo', 'path', 'model', 'retire_date', 'context', 'same_context_as_id', 'label', 'notes'])
        first_seen = {}
        for i, (repo, path, sha, model, d, ctx) in enumerate(rows, 1):
            dup = first_seen.setdefault(ctx, i)          # identical context already listed (a copied skill)
            w.writerow([i, repo, path, model, d, ctx, dup if dup != i else '', '', ''])
    print('frame: %d occurrences, %d repositories, %d distinct texts (%d with text on disk)' % (
        sum(len(v) for v in occ.values()), len(repos), len({s for v in occ.values() for _, s in v}), len(text)))
    print('sampled %d repositories (seed %d); skipped %d with no retired mention found' % (len(rows), SEED, skipped))
    print('distinct repositories:', len({r[0] for r in rows}), '| distinct owners:', len({r[0].split('/')[0] for r in rows}),
          '| distinct skill texts:', len({r[2] for r in rows}), '| distinct contexts:', len({r[5] for r in rows}))
    fam = collections.Counter(re.sub(r'-\d{8}$', '', R.norm(r[3])) for r in rows)
    print('most-sampled models:', fam.most_common(10))
    print('retirement year-month:', sorted(collections.Counter(r[4][:7] for r in rows).items()))


if __name__ == '__main__':
    main()
