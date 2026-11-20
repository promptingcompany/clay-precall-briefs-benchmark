"""Helpers for the Harbor grader, with the same rules as the benchmark's own scorer (scoring/scorers.py).
Standard library only."""
import csv
import glob
import json
import os

YES = {"y", "yes", "true", "1"}
LOGS = os.environ.get("HARBOR_LOGS", "/logs/verifier")


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        return [h.strip() for h in (r.fieldnames or [])], [{(k or "").strip(): (v or "") for k, v in row.items()} for row in r]


def output_dir(default="/app/output"):
    """The agent's output folder arrives as a collected artifact; use whichever copy holds output.csv."""
    found = sorted(glob.glob("/logs/artifacts/**/output.csv", recursive=True))
    return os.path.dirname(found[0]) if found else default


def rate(n, d):
    return round(n / d, 4) if d else None


def yes(v):
    return (v or "").strip().lower() in YES


def missing_columns(header, required):
    return [c for c in required if c not in header]


def write_reward(result, notes):
    """Harbor reads reward.json as numbers: a metric that couldn't be computed (None) is left out, not written as null."""
    os.makedirs(LOGS, exist_ok=True)
    result = {k: v for k, v in result.items() if v is not None}
    with open(os.path.join(LOGS, "reward.json"), "w", encoding="utf-8") as f:
        json.dump(result, f)
    print("\n".join(notes))
    print(json.dumps(result))


def data_missing(names, readme):
    write_reward({"reward": 0, "passed": 0, "data_missing": 1},
                 [f"missing: {', '.join(names)}. This data names real people and is shared on request; see {readme}."])
    raise SystemExit(0)
