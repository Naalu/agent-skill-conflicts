# Project history: how we got here (6–9 October 2026)

A short account for collaborators. The full record, with every rule written before
the data and every correction, is `docs/runlog.md`. All pilot numbers are exploratory and not yet reportable.

## 1. Choosing a direction

We asked which study would give the best chance of a winning challenge paper. Candidates came from the arXiv
literature on agent skills and the GitSkills dataset. Two were piloted: **skill rot** (skills that name AI models
their vendors have retired) and **competing skills** (skills in one repository whose descriptions overlap).
Our advisor's guidance shaped everything after that: sound data-mining practice, principled sampling and
statistics, nothing ornate in 4 pages, strong visuals, extra self-mined data where it pays, and as few avenues of
attack on the findings as possible. He saw particular potential in competing and conflicting skills.

## 2. Skill-rot pilot (Runs 1–3, folder `pilot/rot/`)

- 54,613 valid distinct skills name a model, in 23,806 repositories.
- 32.8% of those repositories named a model already retired when the dataset was collected (cut-off 2026-07-08),
  rising to 53.7% by April 2027 on announced retirements.
- 47.7% of 2,221 flagged skills with commit history were first committed after the model retired.
- Weaknesses: 43% of flagged repositories are flagged only by models retired weeks before collection, and in a
  reading of 60 mentions only about 4 in 10 were operative (the rest tags, examples or tables).
- Corrections made along the way: the collection cut-off (36.0% became 32.8%), a generated skill family that
  inflated counts, and a misquoted figure from Gao et al. All are logged.
- Ready if needed: a 200-mention labelling sample and codebook (`docs/codebooks/retired-model-mentions.md`), and
  `pilot/rot/fetch_first_commits.py` for commit dates (needs your own GitHub token; not yet run).

## 3. Competing-skills pilot (Run 4, folder `pilot/collide/`)

- Rule written before the data: GO only if some cosine cut-off on description embeddings gave at least 80%
  truly competing pairs. 20,000 libraries were embedded (all-MiniLM-L6-v2) and 300 pairs read blind by two readers.
- Verdict: **NO-GO** for a cut-off. The share judged competing rises from about 15% at similarity 0.40 to about
  45% at 0.70 and then stays near one half up to 0.95. High-similarity pairs are often template siblings.
- The phenomenon is real: an estimated 31% (±7) of libraries with two or more skills have a most-similar pair
  judged competing (a floor). Exact duplicates are rare (0.97%).
- Caveat: both readers were LLM instances, so this is not human validation. Hence the 180-pair calibration
  set for two human coders (`labelling/calibration-180/`).

## 4. Literature and documentation review (2026-10-08, `docs/research-brief.md`)

- Every agent product picks skills by having the model read names and descriptions; none de-duplicates by meaning.
- Lab studies show overlap hurts selection; practitioners report the specific skill silently never fires.
- No field measurement of overlap among co-installed skills was found.
- Same-name skills are a different problem: each product resolves them by its own rule.

## 5. Probes motivated by the review (Run 5)

- 12,875 repositories hold skills in two or more agent directories; 9,875 of them repeat a skill name across
  directories; in 3,591 (36%) at least one mirrored copy differs. This became RQ1.
- 2.45% of skills are closed to model invocation and cannot compete; 4.5% of multi-skill libraries exceed an
  8,000-character listing; about 14% of libraries contain a description that names another skill of the library.

## 6. Decision (2026-10-09)

The team adopted the three-question design in `docs/proposal.md`, including a behavioural check, and opened this
repository.
