# Getting started: calibration labelling

A step-by-step guide for both coders, written for people new to Git and GitHub. It covers getting the repository onto
your computer, making your own copy of the pairs, opening it safely in a spreadsheet, labelling, checking your file,
and handing it in. The codebook, [`docs/codebooks/competing-pairs.md`](../docs/codebooks/competing-pairs.md), is the
authority on how to label; this guide only covers the mechanics.

**Deadline:** 2026-10-23 (issue #1). **Time:** 180 pairs; plan several sittings.

## Ground rules (they protect the agreement measure)

- **Label alone.** Do not discuss individual pairs, or show your file, until both coders have finished.
- **Keep your file on your own computer.** The repository is public: anything pushed, on any branch, can be read by
  anyone, including the other coder. Git is already set to ignore files named `coder-*`, so they cannot be pushed by
  accident with the steps below.
- **Never edit `pairs.csv`.** It is the shared original. You work on your own copy.
- The earlier pilot labels and the key with similarity bands are deliberately not in the repository until both of
  you have finished.

---

## Part 1. One-time setup (about 20 minutes)

You type the commands below into a **terminal**: on a Mac, the Terminal app, or in VS Code **Terminal → New
Terminal**; on Windows, PowerShell, or the same VS Code menu. Paste one command at a time and press Enter.

**1. Accept the invitation.** Open the e-mail or notification from GitHub inviting you to
`Naalu/agent-skill-conflicts` and click **Accept**. Without this you can read the repository but not push to it.

**2. Install Git** (the tool that tracks versions of files).
- Mac: run `git --version`. If a window offers to install the "command line developer tools", click **Install** and
  wait; then run `git --version` again. It should print a version number.
- Windows: download Git from <https://git-scm.com/download/win> and install it with the default options. Close and
  reopen the terminal, then run `git --version`.

**3. Install the GitHub CLI** (`gh`, which signs you in to GitHub from the terminal). Download the installer for your
system from <https://cli.github.com>, run it, then close and reopen the terminal and run `gh --version`.

**4. Sign in to GitHub.**
```
gh auth login
```
Answer the questions: **GitHub.com** → **HTTPS** → "Authenticate Git with your GitHub credentials?" **Yes** →
**Login with a web browser**. Copy the one-time code it shows, press Enter, paste the code in the browser page and
approve. Check with `gh auth status`; it should say "Logged in to github.com account <your handle>".

**5. Set the name and e-mail that appear on your commits.** Commits on a public repository show these to anyone, so
use your GitHub handle and GitHub's private "noreply" address:
1. On GitHub, open **Settings → Emails**, tick **Keep my email addresses private**, and copy the address shown there
   (it looks like `12345678+handle@users.noreply.github.com`).
2. Run, with your own values:
   ```
   git config --global user.name "your-github-handle"
   git config --global user.email "12345678+handle@users.noreply.github.com"
   ```

**6. Clone the repository** (download your own linked copy of it).
- Mac:
  ```
  cd ~/Documents
  gh repo clone Naalu/agent-skill-conflicts
  cd agent-skill-conflicts
  ```
- Windows:
  ```
  cd $HOME\Documents
  gh repo clone Naalu/agent-skill-conflicts
  cd agent-skill-conflicts
  ```
This creates the folder `Documents/agent-skill-conflicts`. Check that the calibration files are there: on a Mac
`ls labelling/calibration-180`, on Windows `dir labelling\calibration-180`. You should see `pairs.csv` and
`pairs.csv.translation.json`.

From now on, every command in this guide is run **inside that folder**. If you open a new terminal later, first run
`cd ~/Documents/agent-skill-conflicts` (Windows: `cd $HOME\Documents\agent-skill-conflicts`).

---

## Part 2. Make your own copy

**1. Get the latest version** of the shared files:
```
git pull
```

**2. Copy `pairs.csv` to your own file.** Agree with the other coder who is A and who is B; the commands below use
`coder-b.csv` (use `coder-a.csv` if you are A).
- Mac: `cp labelling/calibration-180/pairs.csv labelling/calibration-180/coder-b.csv`
- Windows: `Copy-Item labelling\calibration-180\pairs.csv labelling\calibration-180\coder-b.csv`

**3. Confirm Git ignores it:**
```
git status
```
It should say `nothing to commit, working tree clean`; your file is not listed because Git ignores it. If your file
**is** listed, stop and tell the other team member before doing anything else.

---

## Part 3. Open the file in a spreadsheet

The file holds Chinese, Japanese, Korean and other scripts, so how you open and save it matters. A spreadsheet can
quietly change text when it saves; the checker in Part 5 catches this. Pick one app and stick with it.

What you will see, one row per pair:

| Columns | What they are |
|---|---|
| `id` | Pair number |
| `name_a`, `description_a`, `name_b`, `description_b` | The two skills, exactly as an agent sees them |
| `lang_a`, `lang_b`, `needs_translation` | Detected language; `yes` marks the 29 non-English pairs |
| `name_a_en` … `description_b_en` | Machine translation into English (filled only when `needs_translation` is `yes`) |
| `label`, `type`, `notes` | **Your columns**, the only ones you type in |

### Excel (Mac or Windows)
1. **Open:** File → Open → `labelling/calibration-180/coder-b.csv`. Scroll to a row where `needs_translation` is `yes`
   and check the original text shows real characters (for example 中文 or 日本語), not symbols such as `ä¸­æ`. If it
   looks garbled, close **without saving** and use LibreOffice below.
2. **Make it readable:** View → Freeze Top Row; select the description columns and turn on Wrap Text; widen them;
   right-click the `lang_a` and `lang_b` column letters → Hide.
3. **Save:** File → Save As → File Format **CSV UTF-8 (Comma delimited) (.csv)**, same name, same folder → Replace.
   If Excel warns that some features may be lost, choose to keep the CSV format. Use exactly this format every time
   you save.

### LibreOffice Calc (free, Mac or Windows; the safest choice)
1. **Open:** File → Open → `coder-b.csv`. In the Text Import window set **Character set: Unicode (UTF-8)**,
   **Separated by: Comma** only, **String delimiter: "**, and tick **Format quoted field as text**. Click OK.
2. **Make it readable:** View → Freeze Cells → Freeze First Row; wrap and widen the description columns.
3. **Save:** File → Save → **Use Text CSV Format!** If asked for options: Unicode (UTF-8), comma, quote `"`.

### Numbers (Mac)
1. **Open:** right-click `coder-b.csv` in Finder → Open With → Numbers.
2. **Save:** File → Export To → CSV… → Advanced Options → **Text Encoding: Unicode (UTF-8)** → Save as `coder-b.csv` in
   `labelling/calibration-180`, and Replace. (If Numbers also asks to save a `.numbers` file, name it `coder-b.numbers`
   in the same folder; Git ignores that too.)

**In every app:** do not sort the rows, do not add or delete rows or columns, and do not edit any column other than
`label`, `type` and `notes`. Close the file before running the checker.

---

## Part 4. Label

Read the whole codebook, [`docs/codebooks/competing-pairs.md`](../docs/codebooks/competing-pairs.md), before you
start, and keep it open while you work. Quick reference only; the codebook wins if they ever seem to differ:

| Column | What to type |
|---|---|
| `label` | **C** competing, **N** not competing, **U** cannot tell. One capital letter. |
| `type` | Only when `label` is C: **D** duplicate or variant, **S** one scope contains the other, **O** partial overlap. Leave empty otherwise. |
| `notes` | Optional. When torn, write the other label you considered. When a pair is U because of language, write `language`. |

- Judge each pair from the text in the file only, as the agent would; do not look the skills up elsewhere.
- **Non-English pairs:** read the original and the `*_en` translation side by side. If you read the language yourself,
  the original wins. Do not translate anything yourself or use online translators while labelling.
- Save often (in the format from Part 3). You can change a label until you hand the file in.
- Keep a backup now and then by copying your file to a folder **outside** the repository (for example
  `Documents/labelling-backup/`), not to a shared drive the other coder can open.

---

## Part 5. Check your file

Run this at any time, as often as you like. It only reads your file and never changes it.
- Mac: `python3 labelling/check_labels.py labelling/calibration-180/coder-b.csv`
- Windows: `py labelling\check_labels.py labelling\calibration-180\coder-b.csv`

It reports how many pairs are labelled, which are still blank, and any problem to fix, for example:

| Message | What to do |
|---|---|
| `label 'c' should be C, N or U` | Retype it as a capital letter. |
| `label C needs a type D, S or O` | Add the type for that pair. |
| `type 'D' is only used with label C` | Clear the type, or change the label. |
| `... changed compared with pairs.csv` | Text in that row was edited or altered on save. Copy the original cell from `pairs.csv` (open it, copy, close without saving), or ask the other team member. |
| `saved with ';' separators` | Your spreadsheet saved with semicolons (common with European regional settings). Save again with LibreOffice as in Part 3. |
| `not saved as UTF-8` | Save again using the exact format in Part 3. |
| `Row order changed` / `Expected 180 rows` | Rows were sorted, added or deleted. Start again from your latest backup or a fresh copy. |

When every pair is labelled and there are no problems, it prints **Finished: every pair has a label.**

---

## Part 6. When you have finished

1. Run the checker one last time and make sure it says **Finished**.
2. Add a comment to issue #1 on GitHub saying only "Coder B finished" (or A). Do not attach the file or mention any
   labels or counts.
3. Keep the file where it is and keep not discussing pairs until both coders have posted.

## Part 7. Handing in (only after both coders have finished)

The lead author starts a branch called `calibration-labels`. On that branch the blind-labelling block is removed
from `.gitignore`, `coder-a.csv` and the earlier pilot labels are added, and the branch is pushed. The second coder
then adds their file to the same branch:
```
git fetch
git switch calibration-labels
git status
```
`git status` should now list `labelling/calibration-180/coder-b.csv` as untracked. Add **only that file**, commit and
push:
```
git add labelling/calibration-180/coder-b.csv
git commit -m "Add coder B calibration labels"
git push
```
Both files then arrive in `main` together through one pull request, Cohen's kappa is computed, and the result is
recorded in `docs/runlog.md` (issue #1).

---

## If something goes wrong

| Problem | Likely cause and fix |
|---|---|
| `gh repo clone` says it could not resolve the repository | The invitation is not accepted yet, or you are signed in to another account (`gh auth status`). |
| `git pull` says local changes would be overwritten | A shared file (often `pairs.csv`) was edited. Do not force anything; ask the other team member. |
| `git status` lists your `coder-…` file | Do not commit. Tell the other team member. |
| Text shows as symbols like `ä¸­æ` | The file was opened with the wrong encoding. Close without saving and open it with LibreOffice (Part 3). |
| A command says "not a git repository" | You are not inside the repository folder; `cd` into it (end of Part 1). |
