"""Run 4 follow-up: unmask the low-band reading (0.40-0.70) and extend the stratified estimate.
Post-hoc: this reading was added after the Run 4 verdict and is not part of the pre-written rule."""
import pandas as pd, numpy as np
pd.set_option('display.width', 200)
key = pd.read_parquet('out/label_key_low.parquet')
A = pd.read_csv('out/labels2_readerA.csv'); B = pd.read_csv('out/labels2_readerB.csv')[['pid', 'label']]
d = key.merge(A.rename(columns={'label': 'A'}), on='pid').merge(B.rename(columns={'label': 'B'}), on='pid')
assert len(d) == 80 and set(d.A) <= set('CNU') and set(d.B) <= set('CNU')
d[['pid', 'set', 'lo', 'sim', 'lib_id', 'old_pid', 'A', 'B']].to_csv('out/labels2_joined.csv', index=False)

def kappa(x, y):
    cats = sorted(set(x) | set(y)); po = (x == y).mean()
    pe = sum((x == c).mean() * (y == c).mean() for c in cats)
    return po, (po - pe) / (1 - pe)

po, k = kappa(d.A, d.B)
print(f"round 2: n=80  A: {d.A.value_counts().to_dict()}  B: {d.B.value_counts().to_dict()}  agreement {po:.3f}  kappa {k:.2f}")
low = d[d.set == 'LOW']
print(low.groupby('lo').agg(n=('pid', 'size'), A_C=('A', lambda s: (s == 'C').sum()), B_C=('B', lambda s: (s == 'C').sum())))

# anchors: same pair read twice by each reader (round 1 vs round 2)
j1 = pd.read_csv('out/labels_joined.csv').rename(columns={'a': 'A1', 'b': 'B1', 'pid': 'old_pid'})[['old_pid', 'A1', 'B1']]
an = d[d.set == 'ANCHOR'].merge(j1, on='old_pid')
print(f"anchors n={len(an)}: reader A same label both rounds {(an.A == an.A1).sum()}/20, reader B {(an.B == an.B1).sum()}/20")
print(an[(an.A != an.A1) | (an.B != an.B1)][['pid', 'old_pid', 'sim', 'A1', 'A', 'B1', 'B']])

# stratified estimate over libraries, strata = band of the library's most similar pair
lm = pd.read_parquet('out/pairs_libmax.parquet'); N = 20000
r1 = pd.read_csv('out/labels_joined.csv'); r1 = r1[r1.set == 'L'].rename(columns={'a': 'A', 'b': 'B'})[['lo', 'A', 'B']]
allL = pd.concat([r1, low[['lo', 'A', 'B']]])
edges = [0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0001]
rows = []
for lo, hi in zip(edges[:-1], edges[1:]):
    Nb = int(((lm.max_sim >= lo) & (lm.max_sim < hi)).sum()); s = allL[np.isclose(allL.lo, lo)]
    rows.append(dict(lo=lo, N_lib=Nb, share=Nb / N, n=len(s), pA=(s.A == 'C').mean(), pB=(s.B == 'C').mean()))
t = pd.DataFrame(rows); print(t.round(3).to_string(index=False))
print("libraries with most similar pair < 0.40 (not read):", int((lm.max_sim < 0.40).sum()) + (N - len(lm)), f"{((lm.max_sim < 0.40).sum() + N - len(lm)) / N:.3f}")
def est(t, col):
    p = (t.share * t[col]).sum(); se = np.sqrt((t.share ** 2 * t[col] * (1 - t[col]) / (t.n - 1)).sum()); return p, 1.96 * se
for name, sub in [('>=0.70', t[t.lo >= 0.70]), ('0.40-0.70', t[t.lo < 0.70]), ('>=0.40', t)]:
    for r in ['pA', 'pB']:
        p, h = est(sub, r); print(f"  {name:10s} reader {r[1]}: {100 * p:.1f}% +/- {100 * h:.1f}")
