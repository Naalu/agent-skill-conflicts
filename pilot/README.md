# Pilot code and results (6–8 October 2026)

Exploratory pilots for the MSR 2027 Mining Challenge: retired-model references in agent skills (Runs 1-3) and
competing skills inside one library (Runs 4-5, folder `collide/`). Runs 1-3 live in `rot/`.
Nothing here is a reportable finding. `../docs/runlog.md` is the record of what was run and what changed.
The scripts were written in a cloud sandbox and are kept as they ran; paths are relative to the folder each
script sits in. Large intermediate files (downloads, DuckDB databases, embeddings) are not committed, and neither are
row-level files that name repositories (kept in `../data/private/`; regenerate them with the scripts, or ask the team).

## Layout

| Path | What it is |
|---|---|
| `rot/expiry/` | Vendor deprecation pages as fetched 2026-10-06, and `retirements.csv` (235 identifiers) |
| `../data/private/label_sample.csv` | 200 mentions to hand-label, one per repository (Run 3); not committed |
| `../docs/codebooks/retired-model-mentions.md` | Codes and procedure for the two coders |
| `../data/private/flagged_occurrences_at_collection.csv` | Files naming a model retired before collection (cut-off 2026-07-08); not committed |
| `../data/private/flagged_occurrences.csv` | Same with the superseded 2026-07-31 cut-off; not committed |
| `rot/data/expiry_curve.csv`, `rot/data/monthly_trends.csv` | Month-level series from Runs 1-2 |

## Skill-rot scripts (`rot/`)

Run 3 scripts work from a directory holding `flagged_occurrences.csv`, `resolve_only.py` and `expiry/retirements.csv`:

1. `fetch_flagged.py 0 31` downloads each artifacts file and keeps the text of flagged skills in `flagged/`.
2. `redraw_sample.py [N] [SEED]` draws the labelling sample.
3. `fetch_history.py 0 31` keeps commit-history fields in `hist/`; `born_stale.py [CUTOFF]` reports born-stale shares.
4. `fetch_first_commits.py IN.csv OUT.csv` pulls commit dates from the GitHub API (needs `GITHUB_TOKEN`; not yet run).

Runs 1-2 scripts (`slim.py`, `content_scan.py`, `rot.py`, `curve.py`, `context.py`, `born.py`, `q.py`,
`expiry_table.py`) built a local DuckDB database that no longer exists. They document the method and need the
database rebuilt (`slim.py`, then `content_scan.py`) before they run again.

## Run 4: competing skills (`collide/`)

Run in this order from `collide/`. Steps 1-4 need about 1.5 GB of disk and the Hugging Face mirror.

1. `slim_local.py` downloads each artifacts file and keeps the columns needed in `slim/`.
2. `build_tables.py` builds `collide.duckdb` (valid skills, tool-visible libraries).
3. `sample_libs.py 20000 20261008` draws the library sample; `embed.py` embeds the distinct descriptions
   (all-MiniLM-L6-v2, ONNX, fetched from Hugging Face on first run) into `out/emb.npy`.
4. `analyze.py` computes per-library collision statistics and the size-matched null; `report.py` prints the tables.
5. `verify.py` recomputes the collision rates by a separate path; `unmask2.py` joins the second reading to its key.

`collide/out/` holds the results that do not need the downloads: `lib_stats.parquet` (one row per sampled library),
`pairs_libmax.parquet` (most similar pair per library), the blind pair files, both readers' labels and the keys.

The two human coders work from `../labelling/calibration-180/` with `../docs/codebooks/competing-pairs.md`.
Coders must not open `out/labels*.csv`, `out/labels2*.csv` or `out/human_pairs_180_key.csv` until both have
finished; those files hold the earlier labels and the similarity bands.

## Run 5: probes from the literature and documentation review (`collide/`)

Run after the Run 4 steps. All descriptive; definitions are in `../docs/runlog.md` under Run 5.

- `probes.py`: skills mirrored across agent directories and whether mirrors diverged (P1); listing size against
  product budgets (P2).
- `fm_scan.py 0 31` then `probe_p3.py`: front-matter invocation fields such as `disable-model-invocation` (P3).
  `fm_scan.py` downloads each artifacts file again and writes `fm/` (about 44 MB, not committed).
- `probe_p4.py`: negative-trigger wording and cross-references between skills of one library (P4).

`out/human_pairs_180.csv` is version 2 (coders see skill names and original-case descriptions); the blank copy for
the coders is `../labelling/calibration-180/pairs.csv`.
