# Decision log

One row per decision, newest first. Record who decided (by role) and where the evidence is. Never edit an old row;
add a new one that supersedes it.

| Date | Decision | Who | Evidence |
|---|---|---|---|
| 2026-10-09 | Make the repository public; never cite it in the double-anonymous submission (use an anonymised mirror) | Lead author | `docs/challenge.md` |
| 2026-10-09 | Adopt the three-question design: RQ1 mirror drift (exact count, the objective anchor), RQ2 competing skills (stratified sample, two coders), RQ3 behavioural check on about 60 pairs plus author mitigations | Lead author | `docs/proposal.md`, `docs/research-brief.md` |
| 2026-10-08 | Coders label from name plus description in original case, cut at 1,536 characters (what the model is shown) | Proposed in pilot | Run 5 in `docs/runlog.md` |
| 2026-10-08 | Similarity is used only as a sampling stratifier, never as a cut-off | Proposed in pilot | Run 4 verdict in `docs/runlog.md` |
| 2026-10-08 | Competing-skills Run 4: NO-GO for a cosine cut-off on description embeddings (no band reached 80% competing) | Pre-written rule | Run 4 in `docs/runlog.md` |
| 2026-10-08 | Skill-rot study kept as the fallback if the coder-agreement gate fails | Lead author | Runs 1–3 in `docs/runlog.md` |
| 2026-10-06 | Work on the GitSkills dataset and aim for the Best Student Presentation Award | Lead author | `docs/challenge.md` |

## Open decisions

| Question | Owner | Needed by |
|---|---|---|
| Is kappa ≥ 0.60 on the 180-pair calibration set the right gate? | Both coders, advisor | Before calibration labelling ends (2026-10-23) |
| Approve or replace the draft thresholds in the pilot rules (10%, 2×, 80%) | Advisor | Before the main study's rules are written |
| Which agent, model version and budget the behavioural check uses | Lead author, advisor | 2026-10-30 |
| Licence for code and data (needed for Zenodo) | Lead author, advisor | Before the Zenodo upload |
| Anonymised code link for the double-anonymous submission | Lead author | 2026-12-18 |
