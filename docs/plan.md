# Plan to submission (version of 2026-11-17)

Supersedes the version of 2026-11-02 and the milestones in `docs/proposal.md`. Fixed dates: presentation Dec 3,
course paper Dec 9, MSR abstract Dec 18, MSR paper Dec 23. The course paper is the full draft and the MSR version is
a tightened copy of it.

## What we are trying to win with

Framing agreed with the advisor on 2026-11-17. The paper's case, in order of importance:

1. The coverage gap. In the repositories it contains, the dataset holds about 61% of the skill files that were there
   during mining. We measure it with intervals, show the cause (single-byte size buckets over the 1,000-result
   search cap), and demonstrate a repair that costs two API calls per repository. This affects every study built on
   the dataset, and the tone is "characterise and repair".
2. RQ1 measured both ways. For the same sampled repositories, drift between mirrored copies across agent
   directories is computed once from the dataset's rows and once from the repositories' trees at the snapshot. The
   difference shows that the gap changes answers, not only counts.
3. Every number is pre-registered and reported over declared populations with an exclusion cascade. The run log is
   the evidence.
4. RQ2, optional: a human-labelled estimate of competing skill pairs on about 300 pairs, next to Yan et al. Run only
   if the week of Nov 28 allows; dropped first if it does not.

What we are not doing: the behavioural experiment, topic clustering of competing pairs, trends by month, the D/S/O
relation types as a headline result (kappa 0.11; exploratory only), and the checker tool (dropped to make room).
The dataset authors are contacted after submission, not before.

## Population ladder (to be written into the run log before any main-study number is computed)

Report every RQ over each rung. P0 is the dataset; P2 is the headline population for RQ1.

| Rung | Definition | Rule source |
|---|---|---|
| P0 | 120,929 repositories with at least one valid skill under a root agent directory | Checkpoint 1 |
| P1 | P0 minus `fork = true` | Kalliamvakou et al.; Gao et al. |
| P2 | P1 minus collection/distribution repositories: name or description matches the Gao et al. keyword list (awesome, collection, tutorial, course, registry) extended with marketplace, plugins, catalog, library, hub, or `-skills` as a name affix; or skill count above the Tukey upper fence of our own per-repository distribution; or no detected language and no canonical-location skill and two or more skills | Gao et al. 2607.00911 (keywords, Tukey fence); the language rule is ours |
| P3 | P2 with near-fork and template clusters collapsed: repositories whose sorted set of skill content hashes is identical, or has Jaccard >= 0.8 with at least five shared skills, keep one representative (earliest first commit, else most stars) | adapted from Spinellis et al. 2020 and Yan et al.'s family threshold; ours |

Skill-level exclusions applied at every rung: invalid or missing front matter; empty name or description;
fewer than ten instruction lines (Yan et al.); fewer than five meaningful tokens after stopwords (Zhu et al.);
body that is mainly TODO/FIXME or template variables; `disable-model-invocation: true` for RQ2 only.

Bulk/generated flag (sensitivity, not exclusion): skill count above the fence and, where history exists, 90% of
skills sharing a first-commit date; or at least half the skills sharing one body skeleton (same headings, same order).
Report the share of occurrences held by the largest 1, 10 and 100 repositories.

Validation of the P2 classifier: a stratified random sample of 200 repositories (by predicted class and skill-count
band), double-coded from README and file listing via the GitHub API, reporting kappa and per-class precision and
recall. The same API pull answers the byte-exact-duplicate question (are identical copies within a repository
present as separate rows): count SKILL.md paths on GitHub against rows in the dataset.

## Schedule

### Done by Nov 17
- Checkpoints 1 and 2; calibration (kappa 0.61); codebook v4; working set v1 and the population ladder.
- Coverage measured on the 200-repository validation sample, with the window check; cause verified live.
- Private repository for the dataset authors: reproduction, per-repository counts, repair script. Held until after
  submission.
- Validation instrument version 2: material rebuilt as of the snapshot with translations; new coder guide; both
  coders agreed.
- RQ1 tree-based sample designed and logged.

### Nov 18: last working day before the break
- Draw the RQ1 sample and start the fetch (`src/rq1_tree_sample.py`; about 6,000 API calls, runs unattended).
- Commit and merge the design, the script and this plan.

### Nov 19 to 23: nothing required
- One coder is travelling and the other has examinations on Nov 24.

### Nov 23 to 25: validation labels
- Both coders label all 200 repositories with the version 2 guide, about three hours each, files kept local.
- Nov 25. Exchange files; kappa (all, translated versus English, and sids 51 to 200 alone); precision and recall
  of the P2 rule; apply the logged fallback if collection precision is below 0.80.
- Nov 25. `src/rq1_estimate.py` written and run: RQ1 from trees and from dataset rows, coverage on 2,300.
- Nov 25. Decide whether RQ2 goes ahead. If yes, draw about 300 pairs with catalogs rebuilt from snapshot trees.

### Nov 26 to 27: Thanksgiving

### Nov 28 to Dec 3: analyse, freeze, present
- Nov 28 to Dec 1. Figures: coverage by stratum; RQ1 dataset versus tree; cascade table. RQ2 pairs labelled if
  going ahead (about four hours each).
- Dec 1. Coverage, RQ1 and validation results frozen: no number changes after this without a run-log entry.
- Dec 2. Slides and one rehearsal. Structure: what skills are, the catalogue-with-missing-books picture, the
  61% figure and its cause, RQ1 both ways, the repair, what dataset users should do.
- Dec 3. Presentation. RQ2 shown as preliminary or as future work.

### Dec 4 to 9: course paper
- Dec 4 to 5. RQ2 agreement and estimates if it ran; frozen Dec 5.
- Dec 4 to 8. Full draft in the MSR format; advisor comments in; replication package assembled (code, aggregates,
  labels, guides, cascade; no skill text, no repository names).
- Dec 9. Course paper submitted.

### Dec 10 to 23: MSR
- Dec 10 to 17. Tighten to the page limit; anonymise (no names, no repository URL, anonymised code mirror);
  Zenodo package uploaded with a DOI reserved.
- Dec 18. Abstract registered.
- Dec 23. Paper submitted. The dataset authors are sent the private repository afterwards.

## Decisions in force
- Coverage leads; RQ1 is reported from dataset rows and from trees for the same repositories.
- Headline population for RQ1 is P2. P1 is the frame for coverage. P3 and the bulk flag are sensitivity runs.
- RQ2 is optional, on about 300 pairs, drawn only from catalogs rebuilt at the snapshot.
- The pilot labels for the first 50 validation repositories are a record and are not scored.

## What can go wrong and what we do
- The P2 rule validates badly (collection precision under 0.80): fall back to the Gao et al. rules alone (keywords
  and fence), which are citable as published, and report ours as an attempted refinement.
- Validation kappa is low under the version 2 guide: report it, resolve disagreements together, and present the
  P2 results with and without the disputed repositories.
- The fetch does not finish before the break: it is cached and resumable; rerun on Nov 23.
- The 2,300-repository coverage figure differs from the 200-repository one: report both, with the designs, and
  lead with the larger sample.
- Time runs short after Nov 28: RQ2 is dropped first, then the product-directory breakdown of RQ1.
