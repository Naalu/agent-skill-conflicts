"""Run 5 probe P4: boundary wording in descriptions (Run 4 sample of 20,000 libraries).
(a) negative trigger wording; (b) cross-reference = description contains, as a whole token, the name of another
skill in the same library. (b) is reported for names >= 6 characters (as pre-specified) and, stricter, for names
that also contain '-' or '_' (added before computing, to keep ordinary words such as 'review' from matching)."""
import duckdb, re, numpy as np, pandas as pd
con = duckdb.connect('collide.duckdb', read_only=True)
sk = con.sql("select s.lib_id, s.name_norm, s.desc_id, d.text from sskill s join sdesc d using (desc_id) order by lib_id").df()
NEG = re.compile(r"\b(do not|don'?t|never)\s+(use|trigger|invoke|activate|apply|load)\b|\bnot for\b|\bnot (intended|meant|suitable) for\b")
TOK = re.compile(r"[a-z0-9][a-z0-9_\-]*[a-z0-9]")
sk['neg'] = sk.text.str.contains(NEG).astype(bool)
x6 = np.zeros(len(sk), bool); xh = np.zeros(len(sk), bool); pairs = {}
for lib, g in sk.groupby('lib_id', sort=False):
    names = set(g.name_norm); n6 = {n for n in names if len(n) >= 6}; nh = {n for n in n6 if '-' in n or '_' in n}
    for idx, nm, did, t in zip(g.index, g.name_norm, g.desc_id, g.text):
        toks = set(TOK.findall(t)); h6 = (toks & n6) - {nm}; hh = (toks & nh) - {nm}
        x6[idx] = bool(h6); xh[idx] = bool(hh)
        if hh: pairs[(lib, did)] = hh
sk['x6'] = x6; sk['xh'] = xh
L = sk.groupby('lib_id').agg(n=('neg', 'size'), neg=('neg', 'max'), x6=('x6', 'max'), xh=('xh', 'max'))
print(f"skills {len(sk)}: negative-trigger wording {100*sk.neg.mean():.2f}%  cross-reference (name>=6) {100*sk.x6.mean():.2f}%  (hyphenated name) {100*sk.xh.mean():.2f}%")
print(f"libraries {len(L)}: any negative trigger {100*L.neg.mean():.2f}%  any cross-reference (name>=6) {100*L.x6.mean():.2f}%  (hyphenated) {100*L.xh.mean():.2f}%")
for lo, hi in [(2, 5), (6, 20), (21, 10**6)]:
    s = L[(L.n >= lo) & (L.n <= hi)]; print(f"  size {lo}-{hi if hi < 10**6 else '+'}: libs {len(s)}  neg {100*s.neg.mean():.1f}%  xref-hyph {100*s.xh.mean():.1f}%")
# labelled library-max pairs: does either description name the other skill (hyphenated names)?
k1 = pd.read_parquet('out/label_key.parquet'); k1 = k1[k1.set == 'L'][['pid', 'lib_id', 'desc_i', 'desc_j']].merge(pd.read_csv('out/labels_joined.csv')[['pid', 'a', 'b']], on='pid')
k2 = pd.read_parquet('out/label_key_low.parquet'); k2 = k2[k2.set == 'LOW'][['pid', 'lib_id', 'desc_i', 'desc_j']].merge(pd.read_csv('out/labels2_joined.csv')[['pid', 'A', 'B']].rename(columns={'A': 'a', 'B': 'b'}), on='pid')
lab = pd.concat([k1, k2], ignore_index=True)
nm_of = sk.groupby(['lib_id', 'desc_id']).name_norm.apply(set).to_dict()
def xref(r):
    ni = nm_of.get((r.lib_id, r.desc_i), set()); nj = nm_of.get((r.lib_id, r.desc_j), set())
    return bool(pairs.get((r.lib_id, r.desc_i), set()) & nj) or bool(pairs.get((r.lib_id, r.desc_j), set()) & ni)
lab['xref'] = lab.apply(xref, axis=1)
neg_of = sk.groupby(['lib_id', 'desc_id']).neg.max().to_dict()
lab['neg'] = [bool(neg_of.get((r.lib_id, r.desc_i), False) or neg_of.get((r.lib_id, r.desc_j), False)) for r in lab.itertuples()]
print(f"\nlabelled library-max pairs: {len(lab)}")
print(pd.crosstab(lab.xref, lab.a, margins=True).to_string()); print(pd.crosstab(lab.neg, lab.a, margins=True).to_string())
sk[['lib_id', 'desc_id', 'neg', 'x6', 'xh']].to_parquet('out/p4_flags.parquet')
