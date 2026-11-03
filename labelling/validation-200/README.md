# Validation of the repository-type rule (200 repositories)

Purpose: measure how well the P2 rule in `docs/runlog.md` ("Working dataset v1") separates repositories that use
skills from repositories that distribute them. Two coders label 200 repositories independently; the rule's
predictions are compared with the agreed labels afterwards. Design and allocation are in the run-log amendment of
2026-11-02.

## Files

- `sheet.csv`: blank sheet, one row per repository (`sid`, `label`, `notes`). Copy it to `coder-a.csv` or
  `coder-b.csv` and fill in your copy. Do not edit `sheet.csv`.
- `material/<sid>.md`: what you read for each repository (description, top-level folders, skill paths, README
  excerpt). Produced by `src/fetch_trees.py`; not committed because it names repositories and quotes READMEs.
- The coder does not see the rule's prediction, the skill count band, or the repository name beyond what the
  material shows. Do not open `data/private/validation/sample.csv` until both coders have finished.

## Labels

| Label | Use when |
|---|---|
| `project` | The repository is software, a document set, a course site, a personal configuration, or any other thing that the skills serve. The skills are there to help an agent work on the rest of the repository. |
| `collection` | The skills are the product. The repository exists to distribute, catalogue, showcase or sell skills (or plugins, prompts, agents, templates) for others to copy or install. An "awesome" list, a marketplace, a skills pack, a generated library, a template of skills with nothing else. |
| `other` | Neither fits, the repository is gone (status 404), or the material is too thin to decide. Say why in `notes`. |

## Rules

1. Judge from the README and the file list, not from the number of skills. A project with sixty skills is still a
   project; a collection with two skills is still a collection.
2. A dotfiles or personal-configuration repository is `project` (the skills configure that person's agent).
3. A template or starter repository (a scaffold other people generate projects from) is `project` if the template
   is for building something, `collection` if the template is only a set of skills.
4. A monorepo of several tools with a shared skill directory is `project`.
5. A plugin or marketplace repository that also contains the plugin's own source code: `collection` if most of the
   repository is skills and plugin manifests, `project` if the skills are a small part of a larger codebase.
6. If torn, pick one and write the alternative in `notes`.

## Afterwards

`src/validation_agreement.py` (to be written) computes Cohen's kappa between the coders, resolves nothing, and
reports precision and recall of the rule per class, weighted by the sampling weights in `sample.parquet` and
unweighted per cell. The fallback rule in the run log applies if collection precision is below 0.80.
