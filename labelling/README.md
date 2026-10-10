# Labelling

One subfolder per labelling round. Each round has a blank `pairs.csv` and a codebook in `docs/codebooks/`.

## Round 1: calibration (`calibration-180/`)

180 pairs of skills from the same skill directory. Instructions: `docs/codebooks/competing-pairs.md`.

1. Copy `pairs.csv` to `coder-a.csv` or `coder-b.csv` (agree who is which). Never edit `pairs.csv`.
2. Fill the `label` column (C, N or U), the `type` column for C pairs (D, S or O), and `notes` when torn.
3. Label alone. Do not look at the other coder's file, at `pilot/collide/out/labels*.csv`, or at
   `pilot/collide/out/human_pairs_180_key.csv` until both of you have finished.
4. Keep your file on your own computer until both coders are done. The repository is public, so anything pushed,
   on any branch, can be read by anyone, including the other coder. Commit both files together afterwards.
5. When both are done, compute Cohen's kappa (C versus not C) and record the result in `docs/runlog.md`.

The proposed gate: kappa of at least 0.60 before the competing-skills design is adopted.
