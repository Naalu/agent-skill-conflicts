# Conflicting and competing agent skills (MSR 2027 Mining Challenge)

Research repository for a short paper on the [GitSkills](https://arxiv.org/abs/2608.10906) dataset, for the
[MSR 2027 Mining Challenge](https://conf.researchr.org/track/msr-2027/msr-2027-mining-challenge).
The submission is double-anonymous: do not cite or link this repository in it (see `docs/challenge.md`).

The study asks how often a repository gives its coding agents conflicting copies of one skill, how often
differently named skills in one catalogue compete, and whether that changes what an agent does.
The plan is in [`docs/proposal.md`](docs/proposal.md).

## Status

| Stage | State |
|---|---|
| Pilots (skill rot, competing skills, probes) | Done, exploratory; see [`docs/project-history.md`](docs/project-history.md) |
| Direction | Chosen 2026-10-09; see [`docs/decisions.md`](docs/decisions.md) |
| Coder calibration (180 pairs, kappa gate 0.60) | Next; due 2026-10-23 |
| Main study | Not started |

## Layout

| Path | What it is |
|---|---|
| `docs/proposal.md` | The study plan (why, what, how, milestones) |
| `docs/decisions.md` | Decision log and open decisions |
| `docs/runlog.md` | Every rule written before the data, every run, every correction |
| `docs/project-history.md` | Short account of the pilots and how the direction was chosen |
| `docs/research-brief.md` | Literature and vendor-documentation review, with sources |
| `docs/challenge.md` | Submission rules and what they mean for this repository |
| `docs/codebooks/` | Labelling instructions for human coders |
| `labelling/` | Files coders label; one subfolder per labelling round |
| `data/` | Local data, not committed: `raw/` downloads, `interim/` intermediates, `private/` row-level files |
| `pilot/` | Pilot scripts and small results, kept as they ran |
| `src/` | Study code (to come) |
| `paper/` | LaTeX source of the paper (to come) |

## Getting started

```bash
git clone <this repository>
cd gitskills-msr2027
uv sync            # creates .venv with the Python packages in pyproject.toml
```

Pilot scripts run from their own folder; see [`pilot/README.md`](pilot/README.md).

## Working together

- Make a branch for each piece of work, commit small, and open a pull request; another team member reviews.
- Track tasks as GitHub issues, one per milestone or task.
- Before computing any result, write its rule into `docs/runlog.md`.
- Never commit personal information, secrets, or large data files. Row-level pilot files that name repositories
  stay in `data/private/`, which is not committed.
