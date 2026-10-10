# Conflicting and Competing Skills: Study Proposal

Version of 2026-10-09. This file is the authoritative copy; change it through pull requests.

For the MSR 2027 Mining Challenge, we will measure how often a repository gives its coding agents conflicting or
competing skills: copies of one skill that have drifted apart across agent directories, and differently named
skills whose descriptions overlap.

## Why

An agent chooses a skill by reading a list of names and descriptions, and no agent product de-duplicates skills by
meaning. The [Claude Code docs](https://code.claude.com/docs/en/skills) warn that overlapping descriptions can make
it "load the wrong skill or miss one that would help".

Overlap hurts in the lab: one near-synonym competitor per skill cut selection accuracy by 7 to 30%
([Li](https://arxiv.org/abs/2601.04748)). In practice the specific skill silently stops firing
([practitioner audit](https://github.com/laurigates/claude-plugins/issues/2244)). No study has measured how common
this is in real repositories, and prior work flags overlap with similarity cut-offs from 0.45 to 0.95 that are
rarely validated.

Our exploratory pilot found both problems. Of 9,875 repositories that keep the same skill name in two agent
directories, 3,591 (36%) hold at least one copy that has drifted. About 31% (±7) of directories with two or more
skills hold a pair judged to compete, and no similarity cut-off identified competing pairs with 80% precision.

## What

Three questions, with the repository as the unit of analysis:

1. **How often do agents in one repository get conflicting copies of a skill?** An exact count of same-name skills
   whose copies differ across agent directories, and which agents see which copy.
2. **How often do differently named skills in one catalogue compete?** A sampled estimate, by catalogue size and
   by relation: duplicate, general beside specific, or partial overlap.
3. **Does it change what an agent does, and what do authors do about it?** Whether agents pick between competing
   skills inconsistently, and how often authors add cross-references, "do not use for" wording or invocation flags.

## How

- **Data.** The GitSkills July 2026 snapshot (282,200 repositories), its repository metadata, and each product's
  skill-directory rules from vendor documentation.
- **Unit.** The catalogue one product reads: `.claude/skills` for Claude Code, `.agents/skills` for Codex, and the
  union of directories for Copilot, Cursor and OpenCode as a sensitivity check. Skills closed to model invocation
  are excluded, since they cannot compete.
- **RQ1 measures.** Same-name skills across directories, compared by content hash, then classified as description
  changed, body changed, or both. Commit dates show which copy is newer.
- **RQ2 measures.** About 750 pairs drawn by stratified sampling: every pair in small catalogues, and pairs within
  similarity bands in large ones. Two coders label each pair from name and description alone; the study proceeds
  only if Cohen's kappa reaches 0.60 on a 180-pair calibration set.
- **RQ3 measures.** Exact counts of cross-references, negative triggers and invocation flags. A behavioural check
  on about 60 competing pairs: both skills installed, requests built from each description's trigger phrases,
  three runs each in Claude Code, outcome recorded as A, B, both or neither.
- **Analysis.** Design-based prevalence with repository-clustered intervals; relation types by catalogue size;
  clusters of competing pairs by topic; trends by month of first commit. Similarity is used only to stratify,
  never as a cut-off.
- **Limits and ethics.** Personal and plugin skills are not in repositories, so every figure is a lower bound.
  Product rules are those of July 2026, and the behavioural check reflects one model version. Results are reported
  in aggregate, with no personal information.
- **Outputs.** The paper, a Zenodo package with code and labels, and a small conflict checker to demo at the poster.

Proposed milestones: coder calibration by 2026-10-23, RQ1 counts and RQ2 sample drawn 2026-10-30, labels and
behavioural runs 2026-11-13, analysis frozen 2026-11-20, full draft 2026-12-04, abstract 2026-12-18, paper due
2026-12-23.
