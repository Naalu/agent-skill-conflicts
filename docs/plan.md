# Plan to submission (version of 2026-11-02)

Supersedes the milestones in `docs/proposal.md`. Dates are course-first; the MSR deadlines (abstract Dec 18, paper
Dec 23) come after the course paper (Dec 9), so the course paper is the full draft and the MSR version is a tightened
copy of it.

## What we are trying to win with

The paper's case is four things, in this order of importance:

1. RQ1 is new and exact. Nobody has measured drift between mirrored copies across agent directories, and it needs no
   model and no sample. The population ladder below makes it defensible against "your 36% is template noise".
2. Every number is pre-registered and reported over declared populations with an exclusion cascade. The run log is
   the evidence. Reviewers at MSR reward this; most challenge papers do not do it.
3. RQ2 is a human-labelled replication of Yan et al. on thirteen times the repositories, with a codebook, a
   reliability gate, and a design-based estimate. We do not claim to beat them; we claim to measure the same thing
   a different way and report where the two agree and disagree.
4. A small artefact to show at the presentation and poster: a checker that reads a repository and lists its
   conflicting copies and its most-similar pairs. It demonstrates the problem in thirty seconds.

What we are not doing: the behavioural experiment (Yan et al. ran 6,368 sessions; we cannot match it), topic
clustering of competing pairs, trends by month (history covers 24% of contents and is a biased subset), and the
D/S/O relation types as a headline result (kappa 0.11; exploratory only).

## Population ladder (to be written into the run log before any main-study number is computed)

Report every RQ over each rung. P0 is the dataset; P2 is the headline population.

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

### Nov 2 to 8: unblock
- Nov 3. Submit Checkpoint 2. Post for peer review; send our two reviews. (Chris)
- Nov 3. Codebook v4: two rules (workflow stages; one tool on two targets) with a worked request each. Drafted Nov 3,
  edited by both, logged, merged. (Chris drafts, Smirthya edits)
- Nov 4. Run-log entry "working dataset v1" with the ladder, the skill-level rules, thresholds and seed, written
  before the script runs. (Chris, Smirthya reviews)
- Nov 4 to 5. `src/build_working_set.py`: emits the cascade table, the rung membership per repository, the catalog
  fingerprint, the bulk flag, the placeholder flag. (Chris)
- Nov 5. Draw the 200-repository validation sample; pull trees and READMEs via the API; coding sheet. (Chris)
- Nov 5 to 7. Both code the 200 repositories independently (about two hours each). (both)
- Nov 6. Draw the RQ2 main sample from P2: about 750 pairs, stratified by similarity band and catalog size, all pairs
  read in catalogs of two or three skills, seed logged; translate; distribute `pairs.csv`. (Chris)
- Nov 7. RQ1 counts over P0 to P3 at hash level; draw the 100-diff sample from the diverged names in P2; coding
  sheet with three codes (substantive, agent-specific syntax, formatting only). (Chris)
- Nov 8. Fill in Checkpoint 2 Section 6 from the peer feedback; revise the report; merge the PR. (both)

### Nov 9 to 15: measure
- Both label the 750 pairs. At the calibration pace this is 12 to 15 hours each over the week; two sessions of
  two hours a day keeps it honest. Label files stay on each machine until both finish. (both)
- Both code the 100 diffs (about three hours each). (both)
- RQ3 full-population rerun of the pattern counts over P2; which-copy-is-newer on the subset with dates for both
  copies. (Chris)
- Estimator and interval code (`src/estimate.py`): design-based prevalence, repository-clustered bootstrap, by
  catalog size and rung; tested on the calibration set. (Chris)
- Related work and background sections of the paper finished against the final reference list; method section
  rewritten to describe the ladder. (Smirthya)

### Nov 16 to 22: analyse and freeze
- Nov 16. Agreement on the main sample; disagreements resolved together; if kappa is below 0.60, switch to the
  two-bounds report (both-C, either-C) and ask the advisor to adjudicate the disagreements. (both)
- Nov 17 to 18. All estimates, intervals, cascade table, concentration statistics, RQ1 by product and rung,
  RQ3 counts, comparison with Yan et al. (Chris)
- Nov 18. Figures: RQ1 stacked bars by rung; RQ2 dot-and-whisker by catalog size; cascade table. (Chris)
- Nov 19 to 22. Chris is travelling; nothing computational is scheduled. Smirthya drafts results and discussion
  from the frozen numbers; Chris reviews by e-mail. Analysis frozen Nov 22: no number changes after this without a
  run-log entry.

### Nov 23 to Dec 9: write and present
- Nov 23 to 30. Full paper draft in the MSR format on Overleaf; the checker script (`src/check_repo.py`) finished
  and run on three example repositories for the talk. (Smirthya writes, Chris reviews and builds the tool)
- Dec 1. Full draft to the advisor.
- Dec 2. Slides; one rehearsal. Presentation structure: the awesome-quant example, the ladder, the RQ1 number,
  the RQ2 estimate next to Yan et al., what authors do about it, the checker demo.
- Dec 3. Presentation.
- Dec 4 to 8. Advisor and instructor comments in; replication package assembled (code, aggregates, labels,
  codebook, cascade; no skill text); licence chosen.
- Dec 9. Course paper submitted.

### Dec 10 to 23: MSR
- Dec 10 to 17. Tighten to the page limit; anonymise (no names, no repository URL, anonymised code mirror);
  Zenodo package uploaded with a DOI reserved.
- Dec 18. Abstract registered.
- Dec 23. Paper submitted.

## Decisions to take now
- Headline population is P2 (project repositories). P0 and P3 are reported beside it.
- The main sample is drawn from P2 only; the calibration set stays as it is (drawn from P0) and is reported as such.
- Relation types stay in the label file and are reported as exploratory.
- The checker is a stretch goal; if the week of Nov 23 runs short it is dropped before anything else.

## What can go wrong and what we do
- Kappa on the main sample below 0.60: two-bounds report with adjudication, already pre-registered.
- The P2 classifier validates badly (precision under 0.8 for collections): fall back to the Gao et al. rules alone
  (keywords and fence), which are citable as published, and report ours as an attempted refinement.
- The byte-exact check finds dropped copies: re-express RQ1 over the 12,875 repositories with two or more
  directories instead of the 9,875 with a repeated name, and state the correction.
- Labeling runs over: cut the sample to the pairs already labeled, report the achieved n and the resulting interval
  width; do not extend the deadline into the freeze week.
