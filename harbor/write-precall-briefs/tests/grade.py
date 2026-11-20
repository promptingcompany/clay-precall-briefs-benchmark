"""Grader for write-precall-briefs (task T6): the same rules as score_t6 in scoring/scorers.py. A fixed sample
of 20 accounts is rated by the AI reviewer (judge.py) for accuracy, specificity, usefulness and fabrication.
reward = briefs filled / 50; passed needs every brief filled, mean accuracy >= 3.5 and at most 1 fabrication."""
import datetime
import hashlib
import json
import os
import statistics
import sys

from gradelib import output_dir, data_missing, missing_columns, rate, read_csv, write_reward, yes
from judge import review

COLUMNS = ["domain", "bullet_1", "bullet_2", "bullet_3", "first_line"]
ROWS, SAMPLE, FLOOR_ACC, MAX_FAB = 50, 20, 3.5, 1
HERE = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS = os.path.join(HERE, "t6-accounts.csv")
if not os.path.exists(ACCOUNTS):
    data_missing(["tests/t6-accounts.csv"], "harbor/README.md")
_, accounts = read_csv(ACCOUNTS)
RUBRIC = json.load(open(os.path.join(HERE, "task.json"), encoding="utf-8"))["rubric"]   # from scripts/ai_review.py

out = sys.argv[1] if len(sys.argv) > 1 else output_dir()
path = os.path.join(out, "output.csv")
if not os.path.exists(path):
    write_reward({"reward": 0, "passed": 0}, ["output/output.csv missing"])
    raise SystemExit(0)
header, rows = read_csv(path)
miss = missing_columns(header, COLUMNS)
if miss:
    write_reward({"reward": 0, "passed": 0}, [f"missing columns {miss}; header was {header}"])
    raise SystemExit(0)

filled = sum(all((r[c] or "").strip() for c in COLUMNS) for r in rows)
by_domain = {(r["domain"] or "").strip().lower(): r for r in rows}
# The same 20 accounts for every platform and every rerun: the first 20 by hash of the domain.
sample = sorted(accounts, key=lambda a: hashlib.sha256(a["domain"].strip().lower().encode()).hexdigest())[:SAMPLE]
items = []
for a in sample:
    r = by_domain.get(a["domain"].strip().lower(), {})
    items.append({"item_id": a["domain"].strip().lower(), "account_name": a.get("account_name", ""),
                  "contact_title": a.get("contact_title", ""), **{c: r.get(c, "") for c in COLUMNS[1:]}})
scale = {"accuracy": "15", "specificity": "15", "usefulness": "15", "fabricated": ("yes", "no")}
verdicts = review(RUBRIC, scale, items, f"{datetime.date.today()}")
notes = [f"{filled}/{ROWS} briefs filled"]
if verdicts is None:
    mean = {k: None for k in ("accuracy", "specificity", "usefulness")}
    fabrications = None
    notes.append("review skipped: set ANTHROPIC_API_KEY for the verifier to score the briefs")
else:
    mean = {k: round(statistics.mean(float(x[k]) for x in verdicts.values()), 2) for k in ("accuracy", "specificity", "usefulness")}
    fabrications = sum(yes(x["fabricated"]) for x in verdicts.values())
floor = filled == ROWS and mean["accuracy"] is not None and mean["accuracy"] >= FLOOR_ACC and fabrications <= MAX_FAB
result = {"reward": rate(filled, ROWS) or 0, "passed": int(floor), "rows_filled": filled, "reviewed_items": len(items),
          "mean_accuracy": mean["accuracy"], "mean_specificity": mean["specificity"], "mean_usefulness": mean["usefulness"],
          "fabrications": fabrications}
write_reward(result, notes)
