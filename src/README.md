# Study code

The main study's code will live here as small, documented modules. The pilot scripts in `../pilot/` are frozen
records of what ran; when a pilot step is reused, copy it here and adapt the copy rather than editing the original.

## Conventions

- One module per step, with a docstring stating its inputs, its outputs and the `docs/runlog.md` entry it implements.
- Every decision rule, threshold, sample size and seed is written in `docs/runlog.md` before the code that applies it
  is run. The project seed is 20261008 unless a rule says otherwise.
- Python 3.12 managed with uv: `uv sync`, then `uv run python src/<module>.py`.
- Format and lint with Ruff: `uv run ruff format src` and `uv run ruff check src`.
- Read inputs from `data/raw/` or `data/interim/` and write row-level outputs that name repositories to
  `data/private/`; all three are git-ignored. Commit only aggregates and pseudonymous IDs.
