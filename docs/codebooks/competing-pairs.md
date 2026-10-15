# Codebook: do two skills in one library compete?

File: `labelling/calibration-180/pairs.csv` (version 3, 2026-10-15), 180 pairs. Each row holds the name and description of two
skills that sit in the same skill directory of one repository. In each case the pair is the most similar pair in
that library, by an embedding of the descriptions. 20 libraries were drawn at random from each of nine similarity
bands (0.40 to 1.00); the order is shuffled and the similarity is hidden.

Version 3 shows what an agent is given when it chooses: the skill name and the description, in original case,
whitespace-collapsed and cut at 1,536 characters (the Claude Code listing cap). 29 of the 180 pairs have at least
one side that is not in English (Chinese 12, Japanese 8, Spanish 3, Korean 3, Portuguese, Vietnamese and Norwegian
1 each). For those rows `needs_translation` is "yes" and the `*_en` columns hold a machine translation made once,
with one service, for both coders (see `labelling/translate_pairs.py`).

## What you are judging

An agent decides which skill to load from the names and descriptions alone. Judge the pair as the agent sees it.

| Code | Name | Use when |
|---|---|---|
| C | Competing | A realistic request exists for which an agent reading only these two entries could reasonably pick either: they do the same job, or the scope of one contains the scope of the other. |
| N | Not competing | They share a topic, template or wording but differ in object, workflow stage, language, tool or service, or audience, so a realistic request points to one of them. |
| U | Cannot tell | The text is too short or unclear to judge. |

## Decision rules

1. The request must be realistic for this library. "Do something with the code" does not count.
2. Wording that sends the other case elsewhere ("for X use skill Y") counts toward N.
3. Two steps of one workflow (plan, then execute) are N unless one description also claims the other's step.
4. Same job for different versions, variants or copies is C when a request that omits the version fits both.
5. A general skill next to a specific one is C when the general description also covers the specific job.
6. Names count. If only the names tell the two apart, ask whether a user would say that word in the request.
7. Non-English pairs: read the original and the `*_en` translation side by side; judge the pair exactly as you would
   an English one. If you read the language yourself, the original wins over the translation. If the meaning is still
   unclear after both, use U and write "language" in `notes`. Do not translate anything yourself during labelling.
8. If you are torn, pick one and write the other in `notes`.

## `type` (only for C)

| Code | Meaning | Expected failure, from the literature |
|---|---|---|
| D | Duplicate or variant of the same job | The agent picks either; choice can change between runs |
| S | One scope contains the other (general next to specific) | The general skill absorbs requests; the specific one rarely fires |
| O | Partly overlapping scopes | Wrong pick on requests in the shared part |

## Procedure

1. Each coder labels a separate copy and does not see the other's labels or the files `pilot/collide/out/labels*.csv`.
2. Compute Cohen's kappa on C versus not C. Proposed gate: kappa of at least 0.60 before the design is adopted.
   Also report kappa separately for the translated pairs and the English pairs; a gap there is a translation
   problem, not a definition problem.
3. Resolve disagreements by discussion; record the agreed label in a third column.
4. `pilot/collide/out/human_pairs_180_key.csv` maps each `id` to its similarity band and flags pairs that include a skill closed to
   model invocation. Open it only after both coders finish.
