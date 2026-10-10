# Competing and conflicting skills: research brief

Prepared 2026-10-08 for the MSR 2027 Mining Challenge project (GitSkills dataset).
Covers when, how and why agent skills compete, what happens when they do, and what that changes in our study.

**Source marks.** [V] = source opened on 2026-10-08 and the claim confirmed there. [A] = taken from an abstract
or a secondary account only; check against the paper before citing. Pilot numbers are exploratory (run log, Runs 4 and 5).

## Bottom line

1. Every agent product chooses skills the same way: the model reads a list of names and descriptions. No product
   documents retrieval, a classifier or any de-duplication by meaning. Overlap is left to the model.
2. Laboratory work shows overlap hurts. Field prevalence has not been measured by anyone we could find.
3. The usual result is not a wrong pick. It is that the specific skill never fires.
4. Two different things are called a conflict, and they need separate measures: same-name skills, which the
   product resolves by a rule, and differently named skills with overlapping descriptions, which the model resolves.
5. Following the documentation into our data turned up an objective companion finding: skills mirrored across
   agent directories have often drifted apart.

## How selection works

- Agent Skills guide: at startup agents load only name and description, so "the description carries the entire
  burden of triggering". [V]
- Claude Code: "If descriptions are vague or overlap, Claude may load the wrong skill or miss one that would
  help." [V] Each entry is cut at 1,536 characters of `description` plus `when_to_use`. [V]
- Codex: the model starts with each skill's name, description and file path. [V]
- A request that fits two skills has four outcomes: the right one, the wrong one, both, or neither.

## When overlap can matter

| Condition | Evidence |
|---|---|
| Both skills are listed with their descriptions | Claude Code budget is 1% of the context window; over it, descriptions of the least-invoked skills are dropped [V]. Codex: 2% or 8,000 characters; descriptions shortened, then skills omitted [V]. |
| Both are open to model invocation | `disable-model-invocation: true` keeps the description out of context (Claude Code, Cursor) [V]; Codex uses `allow_implicit_invocation` [V]. |
| Both are in the catalogue one product reads | Claude Code reads `.claude/skills`; Codex reads `.agents/skills`; VS Code Copilot reads `.github`, `.claude` and `.agents` together; Cursor also loads Claude and Codex directories [V]. |
| The names differ | Same-name skills are settled by the product: Claude Code personal over project [V]; Codex lists both [V]; VS Code shows both [V]; others first-found or last-loaded [A]. |
| Similarity is middling, not extreme | Chen et al. report a danger band of similarity 0.55 to 0.75 [A; band confirmed in a second summary]. Our pilot: judged competition rises to about 0.70, then stays near one half. |
| The request is vague, or a general skill sits beside a specific one | Chen et al.: "black-hole" skills capture vague requests [V, abstract]. |
| The model is weaker | Li: GPT-4o-mini lost more than GPT-4o [V]. Song and Wei: Haiku abandons skills, Sonnet picks wrong ones [A]. |

## Why overlapping skills end up side by side

Ranked by how often practitioner sources report each cause [A unless marked]:

1. Installers that copy one skill into several agent directories or scopes.
2. One author's catalogue growing sibling skills (six test runners in one plugin [V]).
3. Several packs shipping the same workflow (test-driven development, brainstorming, debugging, code review).
4. Same name in personal, project, plugin and bundled scopes.
5. Broad descriptions, which official guidance encourages: "Err on the side of being pushy" [V]; Anthropic's
   skill-creator says Claude tends to "undertrigger" and asks for "pushy" descriptions [V].
6. A skill that overlaps what the model already does unaided.
7. Old versions kept, vendored upstream skills, agent-generated skills.

## What the result is

| Finding | Source |
|---|---|
| One near-synonym competitor per skill cut selection accuracy by 7 to 30%; two cut it by 17 to 63% (from 100%). Synthetic skills, two models. | Li, arXiv:2601.04748 [V] |
| Routing accuracy falls with the log of library size (R² > 0.97, 15 models, 1,141 real skills); errors concentrate among similar skills; rewriting boundaries raised routing from 71.3% to 91.7%. | Chen et al., arXiv:2605.16508 [V abstract; details A] |
| Pass rate fell up to 21% at 202 skills; the cause was selection, and context overhead was indistinguishable from zero. No-skill runs rose from 12.0% to 38.5%; wrong-skill-only runs from 0% to 7.3%. | Song and Wei, arXiv:2605.24050 [V abstract; split A] |
| Merging two sibling skills raised combined recall from 0.677 to 0.840; misfire rate was 0.14%; a cross-cutting review skill fired on 9 of 50 prompts. | Coder Eval blog, 2026-07-30 [V] |
| 265 skills, 427 sessions: 32 intent clusters "where specialists never fire"; a 17-skill testing plugin had one lifetime use. A later comment notes one cluster never competed because the winner was closed to model invocation. | laurigates/claude-plugins #2244 [V] |
| Curated skills plus distractors: 51.2% to 43.5% task success. | Liu et al., arXiv:2604.04323 [A] |

**Counter-evidence.** When a skill does fire it is usually the right one (precision about 0.96 [V]). Skills fail to
fire about half the time even without overlap (55% and 50% baseline activation in one test [A]). Distinct skills
stay at 100% in Li's test [V]. So overlap is one cause of missed skills among several.

**Gap.** Yin et al. (arXiv:2608.12610) state that no controlled measurement of trigger reliability against
installed-skill count exists [A]. The nearest work is registry-wide name and description matching
(Jia et al., arXiv:2607.01136 [A]). No other paper using GitSkills on this topic was found.

## How others measure it

| Source | Rule for "overlap" | Validated against |
|---|---|---|
| Chen et al. | Similarity band 0.55 to 0.75; near-duplicates above 0.95 removed (bge-m3) | Routing behaviour [A] |
| Zhu et al., arXiv:2603.22447 | Clone classifier, thresholds 0.90 / 0.50 | 300 labelled pairs [A] |
| Kang et al., arXiv:2605.05726 | Cosine 0.80 or more, then an LLM judge | Not reported [A] |
| ToolScope, arXiv:2510.20036 | Cosine above 0.82, then an LLM check | Not reported [A] |
| NVIDIA SkillEvaluator | Cosine 0.95 / 0.90 / 0.75 bands | Not reported [A] |
| drskill | Description similarity 0.6 or more; optional LLM judge | Not reported [A] |
| skill-audit-kit | TF-IDF cosine 0.45 or more; 0.72 gave no hits | One library [A] |
| agentskills.io | Behavioural: 3 runs per query, trigger rate above 0.5 | Guidance [V] |

Cut-offs run from 0.45 to 0.95 and almost none is checked against human judgement or behaviour. Our Run 4
result (no cut-off reaches 80% precision) speaks directly to this.

## What our data adds (Run 5, exploratory)

| Probe | Result |
|---|---|
| Repositories with skills in two or more agent directories | 12,875 of 120,929 (10.6%) |
| Of those, same skill name in two directories | 9,875 (76.7%) |
| Of those, at least one mirrored skill with different content | 3,591 (36.4%); description differs in 1,479 (15.0%) |
| Skills closed to model invocation | 2.45% of skills; 6.8% of multi-skill libraries hold one |
| Run 4 most-similar pairs that include such a skill | 4.1% |
| Multi-skill libraries above an 8,000-character listing | 4.5% (project skills only, a lower bound) |
| Libraries where a description names another skill of the library | 13.8% (6% of small, 48% of large) |
| Libraries with negative-trigger wording | 10.2% |

Not checked: whether mirrored copies differ on purpose, and whether mirror drift has been measured before.

## What changes in the study

1. **Two constructs, two measures.** Same-name conflicts are counted exactly from names and hashes. Competition
   between differently named skills is judged by coders on a sample.
2. **Unit: the catalogue a product reads.** Primary analysis on single directories (`.claude/skills` for Claude
   Code, `.agents/skills` for Codex). Union catalogues (Copilot, Cursor, OpenCode) as a sensitivity analysis.
3. **Drop skills that cannot compete.** Exclude skills closed to model invocation; flag catalogues above the
   listing budget.
4. **Coders see what the model sees.** Name plus description, original case, cut at the product cap. The 180-pair
   file is rebuilt this way.
5. **Code the relation, not only yes or no.** Duplicate or variant; general next to specific; partial overlap.
   Each maps to a failure the literature describes.
6. **No similarity cut-off anywhere.** Similarity only stratifies the sample; the calibration curve is a result.
7. **State the bound.** Personal, plugin and bundled skills are not in a repository, so every figure is a lower
   bound on what an agent lists. Product rules are those of July 2026.
8. **Optional behavioural check.** About 60 pairs run through the agentskills.io protocol, using trigger phrases
   quoted in the descriptions as requests. It answers "judged, not observed" but ties results to one model version.

## Proposed questions

- **RQ1 (exact count):** How often does a repository give agents conflicting copies of one skill?
- **RQ2 (stratified sample, two coders):** How often do differently named skills in one catalogue compete, and
  how does that vary with catalogue size and relation type?
- **RQ3 (exact count):** What do authors do about it (cross-references, negative triggers, invocation flags), and
  does similarity predict competition?

## Could not check

- arXiv full text for Chen et al. and Song and Wei was rate-limited; body-level numbers come from secondary accounts.
- Reddit, X and GitHub issue search were blocked, so practitioner coverage depends on web search.
- Google Scholar and Semantic Scholar citation sweeps were not possible.

## Sources

Papers
- Chen et al., The Scaling Laws of Skills in LLM Agent Systems: https://arxiv.org/abs/2605.16508
- Li, When Single-Agent with Skills Replace Multi-Agent Systems and When They Fail: https://arxiv.org/abs/2601.04748
- Song and Wei, More Skills, Worse Agents?: https://arxiv.org/abs/2605.24050
- Liu et al., How Well Do Agentic Skills Work in the Wild: https://arxiv.org/abs/2604.04323
- Zhou et al., A Single Rewrite Suffices ("skill collision"): https://arxiv.org/abs/2606.30775
- Yin et al., @skills: Attention is all you have: https://arxiv.org/abs/2608.12610
- Jia et al., Skills Are Not Islands: https://arxiv.org/abs/2607.01136
- Zhu et al., skill clone detection: https://arxiv.org/abs/2603.22447
- Kang et al., SkillRet: https://arxiv.org/abs/2605.05726
- Liu et al., ToolScope: https://arxiv.org/abs/2510.20036
- GitSkills dataset: https://arxiv.org/abs/2608.10906

Documentation
- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code features overview: https://code.claude.com/docs/en/features-overview
- Codex skills: https://learn.chatgpt.com/docs/build-skills
- Agent Skills, optimizing descriptions: https://agentskills.io/skill-creation/optimizing-descriptions
- Anthropic skill-creator: https://github.com/anthropics/skills/tree/main/skills/skill-creator
- VS Code agent skills: https://code.visualstudio.com/docs/copilot/customization/agent-skills
- Cursor skills: https://cursor.com/docs/context/skills

Practitioner
- laurigates/claude-plugins #2244: https://github.com/laurigates/claude-plugins/issues/2244
- Coder Eval, Does your Claude Code skill actually trigger?: https://coder-eval.com/blog/does-your-claude-skill-trigger
- Scott Spence, sandboxed activation evals: https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals
- NVIDIA SkillEvaluator: https://docs.nvidia.com/skills/skillevaluator/tier2-deduplication
- drskill: https://github.com/dbreunig/drskill
- skill-audit-kit: https://github.com/chenhz01/skill-audit-kit
