# GitSkills pilot run log

Dataset: mvaccargiu/gitskills (Hugging Face Parquet mirror of Zenodo 10.5281/zenodo.21875637), July 2026 snapshot.
Status of every number in this log: EXPLORATORY. None is a reportable finding.

## Decision rule (written 2026-10-06, before any query on the data)

Overload direction is GO if at least one holds:
- O1 (size): >=2% of harness-visible libraries hold >=64 skills, OR >=10% hold >=32.
- O2 (loudness): >=5% of valid descriptions contain >=1 selection cue.

Rot direction is GO if both hold:
- R1: >=1% of distinct valid skills contain an expiry-bearing reference (named model, runtime or action version).
- R2: >=20% of those contain a reference already expired at the snapshot (2026-07).

Tie-break if both GO: prefer the direction affecting the larger share of repositories.
If neither GO: stop and revisit directions.

Definitions fixed in advance:
- "valid skill" = filename exactly SKILL.md, frontmatter_valid=1, non-empty name and description.
- "library" = set of valid skills sharing one repository and one parent skills directory
  (path with the trailing <skill-folder>/SKILL.md removed).
- "harness-visible library" = library whose directory is one a tool loads from
  (.claude/skills, .agents/skills, .codex/skills, .cursor/skills, .github/skills, .opencode/skills, .gemini/skills ...).
- Thresholds 32/64/128 come from the published library-size sweep; they are yardsticks, not our measurements.

## Log
Tue Oct  6 22:24:03 UTC 2026

### Run 1 — 2026-10-06 (all numbers exploratory; lexicons and regexes NOT yet hand-validated)

Totals reproduced from the dataset paper: 3,797,117 occurrences; 1,877,981 distinct contents; 282,200 repositories.

1. Loadability funnel (occurrences): 3,797,117 all -> 3,742,828 filename exactly SKILL.md -> 3,385,119 valid front matter
   with name+description (89.2%) -> 3,212,667 meeting spec field limits (84.6%) -> 2,875,590 name equals folder (75.7%).
   Distinct contents: 1,877,981 -> 1,612,967 valid (85.9%) -> 1,515,051 spec fields (80.7%).
   Harness-visible (repo-root dot-dir /skills): 843,271 valid occurrences in 141,458 libraries, 120,929 repositories.

2. Library size, harness-visible libraries (n=141,458): median 2, p90 11, p99 52, max 8,009.
   >=32 skills: 2.23%   >=64: 0.73%   >=128: 0.29%.   Skill-weighted: 25.1% of harness-visible skills sit in libraries >=64.
   => O1 NOT MET (needed >=2% at 64 or >=10% at 32).

3. Selection cues in descriptions (distinct valid, n~1.63M):
   loose lexicon 4.12% (read 40 hits: roughly a quarter were real promotion; most were neutral "use this skill whenever <condition>")
   strict lexicon 1.49% (read 30 hits: roughly 60-65% real).
   => O2 NOT MET (needed >=5%).
   Not in the decision rule, observed: description length by first-commit month, never-edited skills:
   median 167 chars (2026-02) -> 265 (2026-07); share >500 chars 3.5% -> 16.8%; share >1,024 (spec cap) 0.07% -> 1.31%.
   "use this skill whenever" phrasing 0.18% (2026-01) -> 2.71% (2026-07).

4. Templates: 957,168 distinct H2-heading signatures over 1,536,554 skills with headings; top 100 signatures cover 8.3%;
   54.4% singletons; exact match to the OpenAI starter template: 0. Largest single signature: 8,203 distinct contents.
   AI co-author trailer on first commit: 30.3% of 450,633 dated skills.

5. Expired references (distinct valid skills, n=1,612,967):
   names a vendor model identifier: 54,624 (3.39%); any expiry-bearing reference (model, Python/Node version, actions pin): 6.76%.
   of those naming a model: 27.3% name one retired by 2026-07-31 (14,896 skills; 0.92% of valid); 37.2% by 2026-10-23.
   occurrences: 34,534; repositories: 7,188 (2.77% of repositories with a valid skill).
   Born stale (dated subset, n=2,164): 48.8% first committed after the model's retirement; never-edited (n=1,539): 53.5%.
   By first-commit AI co-author: 41.0% (n=648) vs 52.2% (n=1,516) -- unadjusted.
   Read 20 flagged skills in context: about 16 present the retired model as usable; about 4 mention it as a warning.
   => R1 MET (3.39% >= 1%), R2 MET (27.3% >= 20%).

DECISION BY THE PRE-SET RULE: Rot = GO. Overload = NO-GO.

Known gaps: gemini-1.x and text-bison retirement dates are from prior knowledge, not the current vendor page; the
runtime-version regexes also match minimum-version statements; history exists for a non-random 458,548-file subset;
July 2026 is a partial month; harness-visible is approximated by any repo-root dot-directory.

### Run 2 — 2026-10-07 (validation of the rot numbers; still exploratory)

Date table: expiry/retirements.csv, 235 identifiers parsed from the three vendor pages (6 rows from prior knowledge).
Resolver: resolve_only.py (exact match, dated-suffix rule, Anthropic alias rule, dead-family fallback).

CORRECTION to Run 1 item 5. Reading 60 retired-model mentions in context showed one repository (ssrjkk/claude-skills)
contributes 4,775 generated skills carrying the front-matter tag "models: [gpt-4, claude-3]". The bare token "claude-3"
is a family name, not a model identifier; it is now excluded.
  Skill level: 54,613 valid distinct skills name a model; 12,143 (22.2%) name one retired by 2026-07-31.
               With the bare token included the figure was 31.1%; with Run 1's hand list it was 27.3%.
  Repository level (one vote per repository): 23,806 repositories have a skill naming a model;
               8,577 (36.0%) have one naming a model retired by 2026-07-31; 53.7% by 2027-04-26 on already-announced dates.
  Born stale: 2,415 dated skills in 1,499 repositories; 43.9% first committed after retirement, median 148 days late;
               45.4% of those repositories have at least one born-stale skill.
               (Earlier variants of the date table gave 48.8% and 56.2%: the estimate is not yet stable.)
  R2 under the corrected definition: 22.2% at skill level (threshold 20%) -- met narrowly; 36.0% at repository level.

Context check (heuristic, +/-90 chars): 98.2% of flagged skills have at least one retired mention with no warning cue nearby.
My reading of 60 mentions (single reader, not a formal validation): about 25 in code/config/CLI as the model to use;
about 20 front-matter or compatibility tags (14 from the one generated family); 6 "e.g." examples; 4 neutral tables;
3 warnings against use; 2 regex artefacts.

Consequence for the design: the repository is the unit of analysis; skill-level figures need cluster-robust intervals;
mentions must be typed (operative / metadata tag / example / warning) before any prevalence claim.

Not done: commit dates for flagged occurrences without history (needs a GitHub token; script fetch_first_commits.py,
input flagged_occurrences.csv). Two-coder labelling of label_sample.csv (200 mentions).

### Run 3 — 2026-10-08 (cut-off correction, sample redraw; still exploratory)

Workspace note: the pilot database (pilot.duckdb) was lost when the cloud workspace was reset. Run 3 was rebuilt from
this package plus the Hugging Face mirror: flagged skill text (fetch_flagged.py) and commit history (fetch_history.py).
Check on the rebuild: born_stale.py with the old cut-off reproduces Run 2 exactly (2,415 skills, 1,499 repositories, 43.9%).

CORRECTION to Runs 1-2: "retired at the snapshot" used a cut-off of 2026-07-31. The dataset's mining runs ran
2026-07-09 to 2026-07-20 (mining_runs table). 17 OpenAI identifiers (gpt-5-codex, gpt-5.1-codex*, gpt-5.2-codex,
gpt-5-chat-latest, ...) were retired on 2026-07-23, after collection, and were wrongly counted. No listed model retired
between 2026-07-01 and 2026-07-22, so any cut-off in that range gives the same result. New cut-off: 2026-07-08.
  Repository level: 7,804 of 23,806 model-naming repositories (32.8%) name a model retired before collection. Was 36.0%.
  Skill level     : 11,231 of 54,613 model-naming skills (20.6%). Was 22.2%. Occurrences: 32,261 (was 34,967).
  The denominators (23,806; 54,613) are carried over from Run 2 and were not recomputed in Run 3.
  The calendar curve (expiry_curve.csv) is unchanged; its 2026-07-31 point (36.0%) is a calendar value, not "at collection".

Born stale under the corrected cut-off (representative copies with history, first commit on or after 2025-10-01):
  2,221 skills in 1,368 repositories; 47.7% first committed after the model's retirement; median 148 days late.
  Never-edited skills: 51.6% (n=1,552). Repositories with at least one born-stale skill: 49.7%.
  By AI co-author trailer on the first commit: 41.1% (n=637) vs 50.4% (n=1,584), unadjusted.
  By when the model retired: before Oct 2025 100% (n=427, by construction); Oct 2025 to May 2026 71.7% (n=710);
  June 2026 11.4% (n=1,084). The pooled figure is a mix of these three groups and depends on the mix.
Recency: 43.4% of flagged repositories are flagged only by models retired in June 2026.
Commit-date-free lower bound: 1,822 repositories (23.3% of flagged; 7.7% of model-naming) name a model retired before
October 2025, i.e. before the skill format was introduced.

Labelling sample redrawn (redraw_sample.py, seed 20261008): frame = 7,804 repositories; simple random sample of 200;
one occurrence, then one retired mention, at random within each. 200 repositories, 200 owners, 182 distinct skill
texts, 171 distinct contexts (29 rows repeat an earlier context: copied skills; column same_context_as_id).
116 of the 200 sampled mentions are of models retired in June 2026. Codebook: label_codebook.md (codes O T E R W N).
The Run 2 sample (label_sample.csv, old definition) is superseded.

GitHub commit-date fetch: use flagged_occurrences_at_collection.csv (32,261 files, 7,804 repositories; about 64,500
requests, roughly 13 hours on one token at 5,000 requests/hour). Not run.

Literature correction: Gao et al. (arXiv:2607.00911) report 53% of reused skills never modified after adoption
(1,295 of 2,462); the 58.8% figure quoted in chat on 2026-10-06 is their share of skills updated at least once.

### Run 4 — 2026-10-08: competing-skills pilot. Decision rule written BEFORE any overlap number was computed.

Why this run: Run 1 judged "overload" by library size and promotional wording only. Whether skills installed
together actually overlap was never measured. The advisor flagged competing/conflicting skills as promising.

Definitions (fixed in advance)
- Valid skill: filename exactly SKILL.md, valid front matter, non-empty name and description (as Run 1).
- Tool-visible library: the valid skills of one repository under one repository-root dot-directory, i.e. a path
  matching ^\.[A-Za-z0-9_-]+/skills/<folder>/SKILL.md (.claude/skills, .agents/skills, .cursor/skills, ...).
  Eligible library: at least 2 valid skills. A repository with several tool directories has several libraries.
- Hard collision (no threshold): two skills in one library with the same name (trimmed, case-insensitive) or the
  same description (whitespace-normalised, case-insensitive).
- Soft collision: cosine similarity of the two descriptions' sentence embeddings >= tau.
  Embedding model fixed in advance: sentence-transformers/all-MiniLM-L6-v2 (fallback if it cannot be installed:
  BAAI/bge-small-en-v1.5). English-centric; non-English descriptions are a known weakness of this pilot.
- Calibration of tau: 30 random within-library pairs per band [0.70,0.75) ... [0.95,1.00), identical descriptions
  excluded. A pair is "competing" if one plausible user request would match both descriptions. tau* = the lowest
  band edge such that that band and every band above it have >= 80% competing pairs (24 of 30).
  Single reader (LLM). Exploratory, not a validation.
- Null: for each library of size n, n skills drawn at random from other repositories' tool-visible skills; same
  statistic. Controls for library size and chance similarity. It does NOT control for a shared project topic.
- Sample: simple random sample of eligible libraries, seed 20261008; size set by a timing test before any
  similarity is computed (all eligible libraries if feasible).

Decision rule: competing-skills direction is GO if all three hold at tau*:
- K1 prevalence : >= 10% of eligible libraries contain at least one soft or hard collision.
- K2 beyond size: the K1 rate is at least 2x the rate in the size-matched null.
- K3 not catalogs only: K1 also holds (>= 10%) among libraries with 2-20 skills.
NO-GO if tau* does not exist (no band reaches 80%) or any of K1-K3 fails.

Reported whatever the verdict: collision rates at tau = 0.80, 0.85, 0.90, 0.95; hard-collision rates; the
skill-weighted share; breakdowns by library size, repository stars and fork status.

Status of the thresholds: 10%, 2x and 80% are draft thresholds, NOT yet approved by the team or the advisor. The full
distributions are saved so any other threshold can be applied without re-running.
rule written 2026-10-08T19:39:45Z

Run 4 progress notes (written before any pair was read)
- Sample: 20,000 of the 82,914 eligible libraries (seed 20261008, md5 ordering): 18,805 repositories, 192,422 skills,
  110,853 distinct descriptions. Full embedding of all eligible libraries would have taken about 75 minutes here.
- Hard collisions, all 82,914 eligible libraries: duplicate name 0.34%, duplicate description 0.88%, either 0.97%
  (0.46% among libraries of 2-20 skills). Hard collisions are rare; K1 will be decided by soft collisions.
- Soft + hard collision rate by tau (sample of 20,000), observed vs size-matched null, and for sizes 2-20:
    tau 0.70: 30.20% vs 1.93%, 2-20: 26.06%      tau 0.85: 6.23% vs 1.36%, 2-20: 4.23%
    tau 0.75: 20.41% vs 1.53%, 2-20: 16.79%      tau 0.90: 3.14% vs 1.34%, 2-20: 1.98%
    tau 0.80: 11.76% vs 1.42%, 2-20:  8.83%      tau 0.95: 1.47% vs 1.33%, 2-20: 0.76%
  Consequence known BEFORE reading pairs: the verdict turns on tau*. GO needs tau* <= 0.75 (at 0.80 K3 fails).
  Because the reader now knows this, the reading is done blind:
- Reading protocol (fixed now):
  Set P (the rule's set): 30 uniformly random within-library pairs per band, 6 bands, 180 pairs.
  Set L (added check): 20 libraries per band chosen uniformly among libraries whose most similar pair falls in the
        band; the pair read is that most similar pair. 120 pairs. K1 is a statement about this pair, so set L is the
        more relevant calibration; set P is kept because the rule named it.
  Both sets are merged and shuffled (seed 20261008); the reader sees two descriptions and no similarity, band or set.
  Labels: C = competing (a realistic request exists for which an agent reading only these two descriptions could
          reasonably pick either: same job, or one scope contains the other); N = not competing (same topic or
          template but different object, stage, language or tool); U = cannot tell (counts as not competing).
  Reader A = an LLM instance that knew the stakes (blind to band). Reader B = a separate LLM instance given
  only the definition and the pairs. tau* per the rule uses reader A on set P. Reader B and set L are robustness
  checks; if they give a different tau*, the verdict is reported as not robust.

Run 4 result (pairs unmasked after both readers finished)
- 300 pairs read blind by two readers. Reader A 124 competing, reader B 127; agreement 97.0%, Cohen's kappa 0.94.
  Both readers are LLM instances, so this agreement is not independent human validation.
- Share judged competing, by similarity band (reader A / reader B):
    Set P (30 random pairs per band): 0.70 33/37%, 0.75 37/40%, 0.80 40/43%, 0.85 37/33%, 0.90 20/20%, 0.95 50/50%
    Set L (20 library-max pairs per band): 0.70 45/50%, 0.75 65/65%, 0.80 40/50%, 0.85 50/50%, 0.90 50/45%, 0.95 45/40%
- No band reaches 80% for either reader or either set, and precision does not rise with similarity.
  High-similarity pairs are often template siblings (same wording, different language, service, stage or hook).
- VERDICT BY THE PRE-SET RULE: tau* does not exist => NO-GO for a collision measure defined by a cosine cut-off on
  description embeddings. K1-K3 are not evaluated because there is no valid tau*.
- What the labels still show (not part of the rule): stratified estimate of the share of eligible libraries whose
  most similar pair (>= 0.70) was judged competing: 15.2% +/- 3.2 (reader A), 16.1% +/- 3.2 (reader B);
  libraries of 2-20 skills: 13.1% / 14.0% +/- 2.9. Pairs below 0.70 were not read (70.1% of libraries have no pair
  at or above 0.70), so this is a floor, not a prevalence. 20 pairs per band; exploratory.

Run 4 follow-up (2026-10-08, POST HOC: added after the verdict above; not part of the pre-written rule)
- Question: the floor above stops at 0.70. Does competition continue below it?
- Reading: 60 more library-max pairs, 20 per band for [0.40,0.50), [0.50,0.60), [0.60,0.70) (2,522 / 3,393 / 4,084
  libraries of the 20,000), plus 20 anchor pairs re-drawn from round-one set L. 80 pairs shuffled (seed 20261009),
  similarity hidden, same definition, same two readers (reader B a fresh LLM instance). Script: unmask2.py.
- Agreement on the 80: 96.3%, Cohen's kappa 0.92. Anchors: reader A gave the same label as in round one on 19 of 20
  (one U -> N), reader B on 20 of 20.
- Share of library-max pairs judged competing, all nine bands (reader A / reader B, n = 20 each):
    0.40 15/20%   0.50 30/30%   0.60 45/40%   0.70 45/50%   0.75 65/65%   0.80 40/50%   0.85 50/50%
    0.90 50/45%   0.95 45/40%
  The share rises with similarity up to about 0.70 and is flat at about one half above it. Similarity orders the
  pairs at the low end and stops separating them at the high end.
- Stratified estimate, share of eligible libraries whose most similar pair was judged competing
  (strata = band of the library's most similar pair; 95% half-width from the within-stratum binomial variance):
    most similar pair >= 0.70:        15.2% +/- 3.3 (A)   16.1% +/- 3.3 (B)     [+/- 3.2 above used n, not n-1]
    most similar pair in 0.40-0.70:   16.2% +/- 6.1 (A)   15.8% +/- 6.1 (B)
    most similar pair >= 0.40:        31.3% +/- 6.9 (A)   31.9% +/- 7.0 (B)
  20.1% of libraries have a most similar pair below 0.40; those were not read and count as zero here.
- Limits: 20 pairs per band; both readers are LLM instances; only the most similar pair per library was read;
  "competing" is judged from the two descriptions alone and no agent was run. Exploratory, not reportable.
- Verification (verify.py, separate code path): naive per-library recomputation over all 20,000 libraries
  reproduces the collision rates at every tau (30.20 / 20.41 / 11.76 / 6.23 / 3.14 / 1.47%), largest difference in a
  library's maximum similarity 8e-7; hard collisions recomputed in SQL on all 82,914 eligible libraries:
  0.34% / 0.88% / 0.97%, as logged.
- Reading of the result: a cosine cut-off is not a valid collision detector (verdict stands). Similarity is still
  usable as a sampling stratifier, with human judgement as the measurement. That is a different design from the one
  the rule tested and needs its own gate before it is adopted: two human coders must reach acceptable agreement on
  out/human_pairs_180.csv.

Run 5 (2026-10-08): descriptive probes motivated by the literature and documentation review
(definitions written before any of these numbers were computed; no go/no-go rule, nothing here is reportable)
Why: the review (research brief, same date) showed that (i) every agent product selects skills by having the model
read a name + description listing; (ii) same-name skills are resolved by the product, by rules that differ between
products; (iii) several products read more than one skill directory of a repository at once; (iv) products cap the
listing and drop or shorten descriptions when it is exceeded; (v) skills can opt out of model invocation, in which
case their description is not listed and they cannot compete. Run 4 treated each directory as one library and
ignored (ii)-(v). These probes size those gaps.
P1 Effective catalogues. Product directory sets, from the product docs read 2026-10-08:
     Claude Code {.claude}; Codex {.agents}; Copilot/VS Code {.github,.claude,.agents};
     Cursor {.cursor,.agents,.claude,.codex}; OpenCode {.opencode,.claude,.agents}; Gemini CLI {.gemini,.agents}.
   Per product: repositories with valid skills in >= 2 of its directories; among them, share with a skill name
   (front-matter name, trimmed, lower-cased) present in two directories; each such cross-directory same-name pair
   classed as identical file (same hash) / same description, different file / different description.
P2 Listing size. Per catalogue: sum over valid skills of len(name) + min(len(description), cap), cap 1,536
   (Claude Code) or 1,024 (spec, Codex). Ignores list formatting and `when_to_use`. Reported as the share of
   catalogues above 5,440 / 8,000 / 16,000 / 40,000 characters. Project skills only, so a lower bound on what an
   agent lists (personal, plugin and bundled skills are not in the repository).
P3 Invocation fields. Front matter = text between the first two '---' lines of the representative copy. Flags:
   disable-model-invocation: true; user-invocable: false; paths; when_to_use. Reported for valid skills in eligible
   libraries, and for the Run 4 most-similar pairs.
P4 Boundary wording. (a) negative trigger: description matches
   (do not|don't|never) (use|trigger|invoke|activate|apply|load) | not for | not (intended|meant|suitable) for;
   (b) cross-reference: description contains, as a whole token, the name of another skill of the same library
   (names of >= 6 characters only). Reported for skills and libraries in the Run 4 sample, and by reader label.
Run 5 results (probes.py, probe_p3.py, probe_p4.py, fm_scan.py; exploratory)
P1 Effective catalogues
- 12,875 of 120,929 repositories with tool-visible skills (10.6%) hold valid skills in two or more agent directories.
- Across any two directories: 9,875 of those repositories (76.7%) carry the same skill name in two directories
  (61,159 mirrored names). In 3,591 of the 9,875 (36.4%) at least one mirrored skill has different file content
  between directories (15,489 names, 25.3% of mirrored names); in 1,479 (15.0%) the description differs; in 1,895
  (19.2%) the body length differs by more than 5% and more than 50 characters (a proxy for a non-trivial change).
  Not checked: whether differences are intentional per-agent adaptations. Content was not diffed.
- By product directory set (repositories with any / with >= 2 of the product's directories / same name in two /
  diverged):  Copilot-VS Code 99,467 / 7,428 / 5,777 / 1,906;  Cursor 97,295 / 8,479 / 6,704 / 2,351;
  OpenCode 91,201 / 6,794 / 5,379 / 1,807;  Gemini CLI 38,087 / 287 / 205 / 69.  Claude Code and Codex read one
  project directory each, so they do not see cross-directory mirrors; they see different copies when mirrors diverge.
P2 Listing size (project skills only; lower bound)
- Single directory, all 141,458 libraries: 4.41% exceed 5,440 characters, 2.62% exceed 8,000, 0.90% exceed 16,000,
  0.25% exceed 40,000. Eligible libraries (>= 2 skills): 7.52% exceed 5,440 and 4.47% exceed 8,000. Median size of
  a library above 8,000 characters: 38 skills. The 1,536 vs 1,024 cap changes these by under 0.05 points.
- Union catalogues (Copilot-VS Code, Cursor, OpenCode): 2.7-2.8% exceed 8,000 characters.
- Reading: listing-budget truncation touches few project-level catalogues; treat as a flagged stratum.
P3 Invocation fields (1,704,819 representative copies with front matter scanned)
- Valid tool-visible skills: disable-model-invocation: true 2.45% (.claude/skills 4.77%, .cursor/skills 5.30%,
  .agents/skills 1.39%); user-invocable: false 1.12%; paths 0.17%; when_to_use 0.58%.
- Eligible libraries: 6.81% contain a skill closed to model invocation; 2.66% have fewer than two open skills.
- Run 4 most-similar pairs: 4.10% include a skill closed to model invocation (2.76% of pairs at >= 0.70), so those
  pairs could not compete in Claude Code or Cursor. Codex's equivalent flag lives in agents/openai.yaml; not scanned.
P4 Boundary wording (Run 4 sample: 192,422 skills, 20,000 libraries)
- Negative-trigger wording: 3.31% of skills; 10.17% of libraries have at least one (6.8% of libraries with 2-5
  skills, 12.3% with 6-20, 29.0% with 21+).
- Cross-reference to another skill of the same library: 11.49% of skills with names >= 6 characters (pre-specified;
  inflated by names that are ordinary words), 4.76% with hyphenated names; libraries with any hyphenated-name
  cross-reference 13.79% (6.2% / 20.8% / 47.9% by the same size bands).
- 180 labelled most-similar pairs: 18 cross-reference each other; reader A judged 8 of those 18 competing, against
  69 of the other 162. Too few to say whether cross-referencing separates pairs.
Change to the human labelling file (same 180 pairs): coders now see the skill name and the description in original
case, cut at 1,536 characters, because the review showed the model is given name + description. The LLM readers
in Run 4 saw lower-cased descriptions without names, so their labels are not strictly comparable. The key file now
flags the 4 pairs that include a skill closed to model invocation.

Repository preparation (2026-10-09)
- Files copied into the team repository. One skill description in the Run 4 reading set contained an e-mail address;
  it was replaced with "[e-mail removed]" in pilot/collide/out/pairs_to_label.txt and label_key.parquet. No label
  or number changes. pilot/collide/embed.py now fetches the model from Hugging Face instead of a sandbox path.

Language handling for RQ2 labelling (2026-10-15; written before any human label was recorded)
- Detector: lingua (all languages, confidence >= 0.60) on name + description, with hand correction of 10 rows the
  detector left undecided (short or code-like English; two Spanish rows; one Japanese side). Calibration set:
  29 of 180 pairs (16%) have a non-English side; all 29 have both sides non-English, in the same language.
  Languages (sides): zh 24, ja 16, es 6, ko 6, pt 2, vi 2, nn 2.
- Rule: non-English pairs stay in the sample (the agent reads them; only the human instrument is limited). One
  person machine-translates them once with one service (DeepL API, EN-US), records service and date in a sidecar,
  and both coders label from original + translation. Coders never translate during labelling. Unclear after both
  -> U with "language" in notes.
- Report kappa for all pairs and separately for translated vs English pairs. Prevalence estimates include
  translated pairs; a sensitivity estimate on English-only pairs is reported alongside.
- Main study: same procedure; language detection is logged per catalogue, and the language mix of the sample is
  reported so readers can judge how far English-only tools (and coders) would have gone wrong.
