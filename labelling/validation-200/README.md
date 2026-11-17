# Validation of the repository-type rule (200 repositories)

Purpose: measure how well the P2 rule in `docs/runlog.md` ("Working dataset v1") separates repositories whose skills
an agent uses where they are from repositories that distribute skills for other people to install. Two coders label
200 repositories independently; the rule's predictions are compared with the agreed labels afterwards. Design and
allocation are in the run-log amendment of 2026-11-02; the changes in this version are in the amendment of
2026-11-17.

Version 2 (2026-11-17). Version 1 was piloted on 50 repositories by one coder. Two problems came up: non-English
material was not translated, and the label definitions left too many repositories in between. The pilot labels are
kept as a record and are not used in the agreement figures. Both coders label all 200 from the version 2 material
with this guide.

## Files

- `sheet.csv`: blank sheet, one row per repository (`sid`, `label`, `notes`). Copy it to `coder-a.csv` or
  `coder-b.csv` and fill in your copy. Do not edit `sheet.csv`.
- `material/<sid>.md`: what you read for each repository, produced by `src/build_validation_material.py`. Not
  committed, because it names repositories and quotes READMEs. It shows the repository as it was at the dataset
  snapshot (July 2026), not as it is today: description, top-level entries, every SKILL.md path (those under a
  root agent directory such as `.claude/skills/` listed apart from the rest), and the README with images, badges and
  HTML removed. Non-English descriptions and READMEs have a DeepL translation below the original; read both, and do
  not translate anything yourself.
- Labels stay on your own machine until both coders have finished. Do not push your file, and do not open the other
  coder's file, `data/private/validation/sample.csv`, or the rule's predictions before then.
- You may open the repository on GitHub if the material leaves you unsure, but remember it may have changed since
  July; the material is what counts. Write "looked on GitHub" in `notes` when you do.

## The question

**Who is meant to use these skills, and where?**

| Label | Answer |
|---|---|
| `project` | An agent working in this repository, or the owner's own agent. The skills help with something: code, a website, documents, a course's exercises, the owner's personal setup. |
| `collection` | Other people, in their own repositories or tools. The skills are what the repository offers: a skills pack, a plugin or marketplace, an "awesome" list, a library, a kit that installs skills elsewhere. |
| `other` | Only when the material cannot answer the question: the repository was gone before we looked and the paths say nothing, or there is no README and the tree shows no purpose. Not for being torn. |

## How to decide

Work through the steps in order and stop at the first one that settles it.

1. **Is there anything to judge?** No README, no description, and only agent-directory files: `other`, note "no
   purpose stated". Deleted repository: judge from the description and paths if they are clear (a top-level
   `skills/` folder of forty skills named after tools is clear), otherwise `other`.
2. **Does the README offer the skills to other people?** Signs: install or copy instructions aimed at the reader
   (`npx skills add`, `/plugin install`, "copy into `~/.claude/skills`", "add to your project"); a list or table of
   the skills with what each one does; words like collection, library, pack, marketplace, awesome; a top-level
   `skills/` or `plugins/` folder rather than an agent directory. If yes and the README is mainly about the skills:
   `collection`.
3. **Is there something the skills serve, and is the README about that thing?** Source code, an app, a site, a
   paper, course material, data, a research project. If yes: `project`, even when the skills are numerous.
4. **Both?** Ask which one the README spends its words on. A tool whose README is about the tool, and which also
   ships a few skills for it, is `project`. A plugin whose README is a catalogue of its skills, with a little glue
   code, is `collection`.
5. **Neither, only skills and a README about them, with no install instructions for others?** If it reads as one
   person's or one team's own setup ("my agent config", dotfiles, "our team's skills"), `project`. If it reads as
   something published for others, `collection`.

If you are still torn, use the tie-breaker: **if every SKILL.md were deleted, would the repository still have a
point?** Yes: `project`. No, and the skills are written for other people: `collection`. Write the other label and the
reason in `notes`.

## In-between cases, decided

Kinds of repository that sit between the labels, with the label they get. They are described in general terms on
purpose; none names a repository in the sample. Add to this table only before labelling starts.

| Kind of repository | Label | Why |
|---|---|---|
| Course or workshop where students clone the repository and run the agent in it to do the exercises | `project` | The skills serve the course's own work, in this repository. |
| Course or tutorial teaching people to write skills, with example skills to copy | `collection` | The examples are meant to be taken elsewhere. |
| "An AI agent that does X", run by opening this repository in Claude Code or Codex | `project` | The skills are the agent's instructions for work done here. |
| The same, but the README says to install the skills into your own agent | `collection` | Used elsewhere. |
| Starter kit or installer that copies agent configuration and skills into other repositories | `collection` | The skills are what is shipped. |
| Application template you generate a new app from, which includes skills for working on the app | `project` | The skills serve the app. |
| Personal dotfiles or agent configuration | `project` | The owner's own agent. |
| Fork or mirror of someone else's collection | `collection` | Same as the original. |
| Monorepo of several tools with a shared skill directory | `project` | The skills serve the tools. |
| Documentation site or knowledge base with skills for writing or maintaining it | `project` | The skills serve the documents. |

Do not use: the number of skills, stars, how good the skills are, or whether you think the repository is serious.

## Notes column

Write a note when you used the tie-breaker, when the translation was hard to follow ("language"), when you looked on
GitHub, or when you chose `other`. Keep it to a few words.

## Afterwards

`src/validation_agreement.py` (to be written) computes Cohen's kappa between the coders, reports it separately for
translated and English repositories, resolves nothing, and reports precision and recall of the rule per class,
weighted by the sampling weights in `sample.parquet` and unweighted per cell. The fallback rule in the run log
applies if collection precision is below 0.80.
