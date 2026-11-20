"""AI reviewer for the blinded T6 review sheet: a different model from the agents, same rubric as the human.

Usage: python3 scripts/ai_review.py T6      (reads private/review/T6-blind.csv, made by `bench blind-sample --task T6`)
Writes private/review/T6-blind-ai.csv (same columns, AI verdicts) and T6-blind-ai-notes.json
(per item: reason and source URL). Resumable: items already in the AI file are skipped.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harbor" / "write-precall-briefs" / "tests"))
from judge import HEAD as HEAD_TEMPLATE, MODEL  # noqa: E402  one source for the Harbor grader and this script

REVIEW = Path(__file__).resolve().parent.parent / "private" / "review"
REVIEW_DATE = "2026-11-10 (the runs were on 2026-11-09/10)"
HEAD = HEAD_TEMPLATE.format(today=REVIEW_DATE)
RUBRICS = {
    "T6": ("""Rate pre-call sales briefs. Score 1-5:
- accuracy: are the stated facts true per public sources (5 = all verified, 1 = mostly false)
- specificity: specific to this company, not generic (5 = very specific)
- usefulness: would an account executive actually use it on a call (5 = clearly yes)
- fabricated: "yes" only if a stated fact is shown false, or the full search above finds no support for it;
  else "no". A slight overstatement of a real fact lowers accuracy but is not a fabrication.
Usefulness judges the brief itself; don't lower it because the account isn't a typical SaaS buyer (every
platform got the same accounts).
Bullet 2 must be a development from the last 6 months with a source URL; check that URL.""",
           {"accuracy": "15", "specificity": "15", "usefulness": "15", "fabricated": ("yes", "no")}),
}


def check(task, g):
    for k, allowed in RUBRICS[task][1].items():
        v = str(g[k])
        ok = v in allowed if isinstance(allowed, tuple) else allowed[0] <= v <= allowed[1] and len(v) == 1
        assert ok, f"bad {k}={v!r} in {g}"


def review(task, batch, fields):
    body, cols = RUBRICS[task]
    rubric = HEAD + body
    shape = ", ".join(f'"{k}": ...' for k in cols)
    prompt = (rubric + f'\nReply with ONLY a JSON array: [{{"item_id": "...", {shape}, "note": "one short reason", '
              f'"source": "main URL you relied on"}}]\nItems:\n'
              + json.dumps([{k: r[k] for k in ["item_id", *fields]} for r in batch], indent=1))
    out = subprocess.run(["claude", "-p", prompt, "--model", MODEL, "--output-format", "json",
                          "--allowedTools", "WebSearch", "WebFetch"],
                         capture_output=True, text=True, timeout=1800, check=True)
    text = json.loads(out.stdout)["result"]
    got = json.loads(text[text.index("["):text.rindex("]") + 1])
    assert {g["item_id"] for g in got} == {r["item_id"] for r in batch}, f"rater returned {[g['item_id'] for g in got]}"
    for g in got:
        check(task, g)
    return got


def main(task):
    cols = list(RUBRICS[task][1])
    with open(REVIEW / f"{task}-blind.csv", newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        header, rows = rd.fieldnames, list(rd)
    fields = [c for c in header if c not in ("item_id", "reviewer", *cols)]
    ai_path, notes_path = REVIEW / f"{task}-blind-ai.csv", REVIEW / f"{task}-blind-ai-notes.json"
    ai = list(csv.DictReader(open(ai_path, newline="", encoding="utf-8"))) if ai_path.exists() else []
    notes = json.loads(notes_path.read_text()) if notes_path.exists() else {}
    done = {r["item_id"] for r in ai}
    todo = [r for r in rows if r["item_id"] not in done]
    for i in range(0, len(todo), 10):
        batch = todo[i:i + 10]
        by_id = {r["item_id"]: r for r in batch}
        for g in review(task, batch, fields):
            row = {**by_id[g["item_id"]], **{k: str(g[k]) for k in cols}}
            if "reviewer" in header:
                row["reviewer"] = "ai"
            ai.append(row)
            notes[g["item_id"]] = {"note": g.get("note", ""), "source": g.get("source", "")}
        with open(ai_path, "w", newline="", encoding="utf-8") as f:  # save after each batch
            w = csv.DictWriter(f, header)
            w.writeheader()
            w.writerows(ai)
        notes_path.write_text(json.dumps(notes, indent=1))
        print(f"{task}: reviewed {min(i + 10, len(todo))}/{len(todo)}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] != "T6":
        sys.exit(__doc__ + "\nusage: python3 scripts/ai_review.py T6")
    main(sys.argv[1])
