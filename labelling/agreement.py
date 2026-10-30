"""Compare coders' label files for one labelling round.

Usage:
    uv run python labelling/agreement.py labelling/calibration-180/coder-a.csv labelling/calibration-180/coder-b.csv [more files...]

For every pair of files it reports Cohen's kappa on C versus not-C (U counts as not competing, as the codebook says),
raw agreement, kappa on the full C/N/U labels, and the same split by needs_translation. It then writes
<folder>/disagreements.csv listing every pair where any two coders differ, with all labels side by side, so the
coders can discuss them. Nothing here changes the label files.

Kappa's standard error uses the large-sample formula (Fleiss, Cohen and Everitt, 1969), so with 180 pairs a
difference of a few hundredths is noise; read the 95% interval, not the point.
"""
import itertools
import math
import os
import sys

import pandas as pd


def kappa(x, y):
    """Cohen's kappa with its standard error, for two equal-length label sequences."""
    n = len(x)
    cats = sorted(set(x) | set(y))
    po = sum(a == b for a, b in zip(x, y)) / n
    px = {c: sum(a == c for a in x) / n for c in cats}
    py = {c: sum(b == c for b in y) / n for c in cats}
    pe = sum(px[c] * py[c] for c in cats)
    if pe == 1:
        return 1.0, 0.0, po
    k = (po - pe) / (1 - pe)
    se = math.sqrt(po * (1 - po) / n) / (1 - pe)
    return k, se, po


def load(path):
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    name = os.path.splitext(os.path.basename(path))[0].replace("coder-", "").upper()
    df["label"] = df["label"].str.strip().str.upper()
    bad = df[~df["label"].isin(["C", "N", "U"])]
    if len(bad):
        sys.exit(f"{path}: {len(bad)} rows without a valid label (ids {', '.join(bad['id'].head(10))}...)")
    return name, df


files = sys.argv[1:]
if len(files) < 2:
    sys.exit(__doc__)
coders = dict(load(f) for f in files)
base = next(iter(coders.values()))
ids = base["id"].tolist()
for name, df in coders.items():
    if df["id"].tolist() != ids:
        sys.exit(f"coder {name}: ids or row order differ from the first file")

print(f"{len(ids)} pairs, coders {', '.join(coders)}\n")
print(f"{'pair':8} {'subset':12} {'n':>4} {'agree':>6} {'kappa C/notC':>13} {'95% CI':>15} {'kappa C/N/U':>12}")
for a, b in itertools.combinations(coders, 2):
    da, db = coders[a], coders[b]
    for subset, mask in [("all", pd.Series(True, index=da.index)),
                         ("english", da["needs_translation"] == "no"),
                         ("translated", da["needs_translation"] == "yes")]:
        xa, xb = da.loc[mask, "label"], db.loc[mask, "label"]
        if len(xa) < 5:
            continue
        k2, se, po = kappa((xa == "C").tolist(), (xb == "C").tolist())
        k3, _, _ = kappa(xa.tolist(), xb.tolist())
        print(f"{a}-{b:6} {subset:12} {len(xa):4d} {po:6.2f} {k2:13.2f} [{k2-1.96*se:5.2f}, {k2+1.96*se:5.2f}] {k3:12.2f}")
    # where do they disagree? by label combination
    ct = pd.crosstab(da["label"], db["label"], rownames=[a], colnames=[b])
    print(f"\n{a} (rows) vs {b} (columns):\n{ct}\n")

labels = pd.DataFrame({f"label_{n}": df["label"] for n, df in coders.items()})
types = pd.DataFrame({f"type_{n}": df["type"] for n, df in coders.items()})
notes = pd.DataFrame({f"notes_{n}": df["notes"] for n, df in coders.items()})
dis = labels.nunique(axis=1) > 1
out = pd.concat([base[["id", "name_a", "description_a", "name_b", "description_b", "needs_translation"]], labels, types, notes], axis=1)[dis]
path = os.path.join(os.path.dirname(files[0]), "disagreements.csv")
out.to_csv(path, index=False, encoding="utf-8-sig")
print(f"{int(dis.sum())} pairs with any disagreement written to {path}")

# type agreement among pairs every coder called C
allc = (labels == "C").all(axis=1)
if allc.sum() >= 5 and len(coders) >= 2:
    print(f"\n{int(allc.sum())} pairs all coders called C; type agreement on those:")
    for a, b in itertools.combinations(coders, 2):
        ta, tb = coders[a].loc[allc, "type"].str.upper(), coders[b].loc[allc, "type"].str.upper()
        k, se, po = kappa(ta.tolist(), tb.tolist())
        print(f"  {a}-{b}: agree {po:.2f}, kappa {k:.2f}")
