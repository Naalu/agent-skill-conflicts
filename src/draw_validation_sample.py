"""Draw the 200-repository validation sample for the P2 (project versus collection) rule.

Implements the run-log amendment of 2026-11-02 ("Amendment to the validation design"): predicted class x
skill-count band, fixed allocation, seed 20261008. Reads data/interim/working_set.parquet and writes
  data/private/validation/sample.parquet   the drawn repositories with their flags and sampling weight
  data/private/validation/sample.csv       the same, readable
Repository names are row-level data, so both files live under data/private/ (git-ignored).
Usage: uv run python src/draw_validation_sample.py
"""
import os

import numpy as np
import pandas as pd

SEED = 20261008
BANDS = [0, 1, 5, 11, 30, 10**9]
BAND_LABELS = ["1", "2-5", "6-11", "12-30", "31+"]
ALLOCATION = {
    ("collection", "1"): 15, ("collection", "2-5"): 15, ("collection", "6-11"): 15,
    ("collection", "12-30"): 40, ("collection", "31+"): 25,
    ("project", "1"): 15, ("project", "2-5"): 25, ("project", "6-11"): 30,
    ("undetermined", "1"): 7, ("undetermined", "2-5"): 7, ("undetermined", "6-11"): 6,
}


def predicted_class(w: pd.DataFrame) -> pd.Series:
    cls = pd.Series("project", index=w.index)
    cls[w.kw_ext | w.lang_null_rule] = "undetermined"
    cls[w.kw_gao | w.kw_affix | w.over_fence] = "collection"
    return cls


def main():
    w = pd.read_parquet("data/interim/working_set.parquet")
    w = w[w.p1].copy()
    w["pred"] = predicted_class(w)
    w["band"] = pd.cut(w.n_names, BANDS, labels=BAND_LABELS).astype(str)
    rng = np.random.default_rng(SEED)
    parts = []
    for (cls, band), n in ALLOCATION.items():
        cell = w[(w.pred == cls) & (w.band == band)]
        if len(cell) == 0:
            print(f"cell {cls}/{band}: empty, skipped")
            continue
        take = min(n, len(cell))
        idx = rng.choice(cell.index.to_numpy(), size=take, replace=False)
        draw = w.loc[idx].copy()
        draw["cell_n"] = len(cell)
        draw["cell_drawn"] = take
        draw["weight"] = len(cell) / take  # repositories in P1 represented by each drawn one
        parts.append(draw)
        print(f"cell {cls}/{band}: {take} of {len(cell)}")
    s = pd.concat(parts)
    s = s.sample(frac=1, random_state=SEED).reset_index(drop=True)  # shuffle so coders see no pattern
    s.insert(0, "sid", range(1, len(s) + 1))
    os.makedirs("data/private/validation", exist_ok=True)
    cols = ["sid", "repo", "owner", "pred", "band", "n_names", "n_skills", "n_dirs", "has_canonical", "language", "stars",
            "kw_gao", "kw_ext", "kw_affix", "over_fence", "lang_null_rule", "cluster_size", "cell_n", "cell_drawn", "weight"]
    s[cols].to_parquet("data/private/validation/sample.parquet", index=False)
    s[cols].to_csv("data/private/validation/sample.csv", index=False)
    print(f"{len(s)} repositories written to data/private/validation/sample.csv")


if __name__ == "__main__":
    main()
