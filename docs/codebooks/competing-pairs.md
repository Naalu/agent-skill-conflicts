# Codebook: do two skills in one library compete?

Version 4, 2026-11-03. Changes from version 3: rules 9 and 10 added after the 180-pair calibration (A versus B kappa
0.61; 27 of the 33 disagreements fell into the two families those rules cover). The definition of competing is
unchanged. Version 3 (2026-10-15) was used for the calibration set; version 4 is used for the main sample.

Each row of a labelling file holds the name and description of two skills that sit in the same skill directory of one
repository. The order is shuffled and the similarity is hidden. The text is what an agent is given when it chooses:
name and description, in original case, whitespace-collapsed and cut at 1,536 characters (the Claude Code listing
cap). Rows with a non-English side have `needs_translation` = "yes" and the `*_en` columns hold one machine
translation, made once with one service for both coders (`labelling/translate_pairs.py`).

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
9. **Stages of one workflow (extends rule 3).** Two skills that cover different stages of one process are N even
   when they belong to the same family, share a prefix, or would both be used on the same afternoon. Reviewing is
   not writing; committing is not opening a pull request; step 3 is not step 4; gathering requirements is not
   analysing the system. The test is whether a realistic request names the stage. It almost always does, because a
   user asks for the thing they want next.
   - `rust-reviewer` / `rust-coder`. "Review the changes in `src/parser.rs` before I commit" goes to the reviewer;
     "add a `--verbose` flag to the CLI" goes to the coder. **N.**
   - `commit` / `write-pr`. "Commit what I have with a sensible message" and "open a PR for this branch" are
     different asks. **N.**
   - `step03-review` / `step04-review`. Numbered stages of one pipeline; the user is at one of them. **N.**
   - `code` / `test`. "Write tests for the date parser" goes to `test`. **N**, unless the `code` description also
     promises to write tests, in which case rule 5 applies and the pair is C with type S.
   - Still C: both descriptions claim the same stage, or one says "plan and implement" next to one that says
     "implement".
10. **One job on two targets (extends rules 4 and 6).** Two skills that do the same thing to different objects,
    platforms or file types are N when the request would naturally name the target; C when the target is a
    version or variant that a realistic request omits (rule 4).
    - `deslop-prose` / `deslop-code`. "Clean the AI-sounding filler out of `README.md`" names a prose file; "clean
      up this function" names code. A user says which. **N.**
    - `clerk-expo` / `clerk-swift`. The platform is in every realistic request ("add Clerk sign-in to the Expo
      app"). **N.**
    - `capacitor-app-upgrade-v7-to-v8` / `capacitor-plugin-upgrade-v7-to-v8`. App and plugin are different objects
      and the descriptions each say "do not use for" the other (rule 2). **N.**
    - `phaser4-gamedev` / `phaser-gamedev`. "Help me build a Phaser scene with a tilemap" fits both; the version
      is the kind of thing a request omits. **C**, type D.
    - `microsoft-foundry` / `microsoft-foundry-classic`. Same product, two generations; "deploy this to Foundry"
      fits both. **C**, type D or S depending on the descriptions.
    - The dividing question: would the user have to say the distinguishing word to get what they want? If the
      word is a file type, platform, language or object, they would (N). If it is a version number or a product
      generation, they usually would not (C).

## `type` (only for C)

| Code | Meaning | Expected failure, from the literature |
|---|---|---|
| D | Duplicate or variant of the same job | The agent picks either; choice can change between runs |
| S | One scope contains the other (general next to specific) | The general skill absorbs requests; the specific one rarely fires |
| O | Partly overlapping scopes | Wrong pick on requests in the shared part |

Agreement on `type` between the two human coders was 0.40 (kappa 0.11) on the calibration set, so types are
recorded but reported as exploratory unless a later calibration on types alone reaches 0.60. Pick the type that
fits best and move on; do not spend time on it.

## Procedure

1. Each coder labels a separate copy and does not see the other's labels, `pilot/collide/out/labels*.csv`, or any
   key file, until both have finished.
2. Compute Cohen's kappa on C versus not C (`labelling/agreement.py`). The gate of 0.60 was met on the calibration
   set (0.61, 95% CI 0.49 to 0.72). On the main sample, if kappa falls below 0.60 the paper reports two bounds
   (pairs both coders call C; pairs either calls C) and the advisor adjudicates the disagreements.
3. Report kappa separately for translated and English pairs; a gap there is a translation problem, not a
   definition problem.
4. Resolve disagreements by discussion; record the agreed label in a third column. Rules 9 and 10 are not to be
   revised during the main sample; anything they fail to settle goes in `notes` for the next version.
