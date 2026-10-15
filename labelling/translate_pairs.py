"""Fill the *_en columns of a labelling file with machine translations into English.

Why: coders judge each pair from its name and description, and about one pair in six is not in English. Both coders
must see the same translation, produced once by one service, so that translation differences never become label
differences. The originals stay in the file; coders read both.

Service: DeepL (https://www.deepl.com/pro-api). The free plan covers 500,000 characters a month; the calibration set
needs about 8,000. Put the key in the environment, never in a file:

    export DEEPL_AUTH_KEY=...            # macOS/Linux
    uv run --with deepl python labelling/translate_pairs.py labelling/calibration-180/pairs.csv

Only rows with needs_translation == "yes" are sent, and only sides whose language is not "en". Rows already filled
are skipped, so the script can be re-run. A sidecar file <input>.translation.json records the service, the date and
the DeepL model-type setting, for the paper's method section.

Manual fallback: if nobody can get an API key in time, one person pastes each non-English name and description into
the DeepL web app, copies the result into the *_en columns, and writes "deepl-web, <date>" in the sidecar by hand.
Whatever the route, one person translates and both coders use the same file.
"""
import datetime as dt
import json
import os
import sys

import pandas as pd

try:
    import deepl
except ImportError:
    sys.exit("Install the client first: uv run --with deepl python labelling/translate_pairs.py <file>")

path = sys.argv[1]
key = os.environ.get("DEEPL_AUTH_KEY") or sys.exit("Set DEEPL_AUTH_KEY in the environment first.")
client = deepl.DeepLClient(key)

df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
todo = []
for idx, r in df.iterrows():
    if r["needs_translation"] != "yes":
        continue
    for side in ("a", "b"):
        if r[f"lang_{side}"] == "en":
            continue
        for field in ("name", "description"):
            col = f"{field}_{side}_en"
            if r[col].strip() == "" and r[f"{field}_{side}"].strip() != "":
                todo.append((idx, col, r[f"{field}_{side}"]))

print(f"{len(todo)} cells to translate")
if todo:
    results = client.translate_text([t for _, _, t in todo], target_lang="EN-US", model_type="prefer_quality_optimized")
    for (idx, col, _), res in zip(todo, results):
        df.at[idx, col] = res.text
    df.to_csv(path, index=False, encoding="utf-8-sig")

sidecar = path + ".translation.json"
record = {
    "service": "DeepL API",
    "target_lang": "EN-US",
    "model_type": "prefer_quality_optimized",
    "date": dt.date.today().isoformat(),
    "cells_translated_this_run": len(todo),
    "note": "Translations are an aid for human coders; the agent is given the original text.",
}
json.dump(record, open(sidecar, "w"), indent=2)
print("done; record written to", sidecar)
