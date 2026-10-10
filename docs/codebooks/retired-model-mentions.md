# Codebook: retired-model mentions in agent skills

Sample: `data/private/label_sample.csv` (not committed), drawn 2026-10-08 (seed 20261008).
One mention per repository, 200 repositories, from the 7,804 repositories whose skills
name a model retired before the dataset was collected (cut-off 2026-07-08).

## What you are coding

Each row is one mention of a retired model inside a SKILL.md file. The mention is
wrapped in `[[double brackets]]` in the `context` column, with 150 characters either
side. `⏎` marks a line break in the original file.

Code the bracketed mention only, even if other models appear in the context.

29 rows repeat a context already listed, because the same skill was copied into several
repositories. `same_context_as_id` gives the earlier row; give both rows the same label.

## Codes (enter one letter in `label`)

| Code | Name | Use when | Typical cue |
|---|---|---|---|
| O | Operative | The skill uses this model, or tells the agent or user to use it. | `model: "..."` in code or config, a CLI flag, "default model", "use X for ..." |
| T | Tag | The model is listed as metadata, not as an instruction. | Front-matter `models:` list, "compatible with", "tested on" |
| E | Example | The model is an illustration and any model would do. | "e.g.", "such as", a placeholder to replace, sample output |
| R | Reference | A neutral catalog entry with no recommendation. | Pricing or context-window table, list of available models |
| W | Warning | The skill says not to use this model, or that it is retired. | "deprecated", "do not use", "replaced by", "legacy" |
| N | Not a model | The match is not a reference to this model. | Part of a longer unrelated string, a footnote key, a different product |

## Decision rules

1. Code what the skill does with the model, not where the text sits. A fenced code
   block can be O (code the agent is meant to run) or E (a sample marked "e.g.").
2. A default, fallback or mapping target is O.
3. If the context says the model is retired and still configures it, code W.
4. If 150 characters are not enough, open the file at `repo` and `path` on GitHub.
5. If you are torn between two codes, pick one and write the other in `notes`.

## Procedure

1. Each coder works on a separate copy of the CSV and does not see the other's labels.
2. Compute Cohen's kappa on the six codes, and again on O versus everything else.
3. Resolve disagreements by discussion and record the agreed label.
4. Report two numbers with Wilson 95% intervals: the share of rows that are not N
   (precision of the detector) and the share that are O (operative).

With 200 rows, a share near 50% is estimated to within about 7 percentage points.
