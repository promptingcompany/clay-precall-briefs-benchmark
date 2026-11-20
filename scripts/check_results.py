#!/usr/bin/env python3
"""Check that the published numbers match the committed results files.

    python scripts/check_results.py           # exit 1 and show what differs
    python scripts/check_results.py --write   # rewrite the generated blocks: the RESULTS.md table and the README.md headline

Generated blocks sit between `<!-- generated:NAME -->` and `<!-- /generated -->`. Figures in hand-written sentences
are checked, not rewritten (see `sentences`). docs/DATA-DICTIONARY.md must describe every column of the CSVs in results/.
"""
import csv
import difflib
import json
import re
import statistics
import sys
from decimal import ROUND_HALF_UP, Decimal as D
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCORES = ("accuracy", "specificity", "usefulness")


def rnd(value, places):
    return D(str(value)).quantize(D(places), ROUND_HALF_UP)


def read_csv(name):
    with open(REPO / "results" / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def wilson(k, n):
    """95% Wilson score interval for k of n: (low, high) as shares, to two decimals."""
    z = statistics.NormalDist().inv_cdf(0.975)
    p = k / n
    mid, half = p + z * z / (2 * n), z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5
    return tuple(str(rnd(max(0.0, x) / (1 + z * z / n), "0.01")) for x in (mid - half, mid + half))


def pct(share):
    return f"{rnd(D(share) * 100, '1')}%"


def score(col):
    return lambda r: f"{r[col]} ({rnd(r[col + '_ci_low'], '0.1')}–{rnd(r[col + '_ci_high'], '0.1')})"


TABLE = [  # row label, how to show it from a t6-results.csv row
    ("Briefs written, of 50", lambda r: r["briefs_written"]),
    ("Accuracy (1–5)", score("accuracy")),
    ("Specificity (1–5)", score("specificity")),
    ("Usefulness (1–5)", score("usefulness")),
    ("Reviewed briefs with a fabricated fact, of 20",
     lambda r: f"{r['fabrications_of_20']} ({pct(r['fabrication_rate_ci_low'])}–{pct(r['fabrication_rate_ci_high'])})"),
    ("Status", lambda r: r["status"]),
    ("Agent steps (tool calls)", lambda r: r["steps"]),
    ("Minutes", lambda r: str(rnd(r["minutes"], "0.1"))),
    ("Platform credit cost of the run", lambda r: "$" + r["credit_cost_usd"]),
    ("Agent's own model cost, billed separately", lambda r: "$" + r["model_cost_usd"]),
]


def table(rows):
    lines = ["| | " + " | ".join(r["platform"] for r in rows) + " |", "|---" * (len(rows) + 1) + "|"]
    lines += [f"| {label} | " + " | ".join(show(r) for r in rows) + " |" for label, show in TABLE]
    return "\n".join(lines)


def headline(rows):
    """The README's headline sentence, or None if the numbers no longer support it."""
    clay, others = rows[0], rows[1:]
    if clay["platform"] != "Clay" or clay["briefs_written"] != "50" or any(
            D(o["accuracy"]) >= D(clay["accuracy"]) or D(o["credit_cost_usd"]) <= D(clay["credit_cost_usd"]) for o in others):
        return None
    rest = " and ".join(f"${o['credit_cost_usd']} on {o['platform']}" for o in others)
    return (f"Clay's briefs were the most accurate ({clay['accuracy']} of 5), with {clay['fabrications_of_20']} fabricated "
            f"facts found in the 20 briefs reviewed and all 50 written, at the lowest credit cost: about "
            f"${clay['credit_cost_usd']} for the 50 briefs, against {rest}.")


def clay_credits(clay, summary_row, prices):
    """Clay's data credits and action credits, worked back from the costs and the config's price per credit."""
    data = D(summary_row["cost_per_1000_accepted_usd_median"]) * D(clay["briefs_written"]) / 1000 / D(str(prices["data_credits"]))
    actions = D(clay["action_credit_cost_usd"]) / D(str(prices["actions"]))
    return [format(x.normalize(), "f") for x in (data, actions)]


def check_csv(rows, summary, prices):
    """Every column results/summary.csv also has must say the same thing; costs must add up; intervals must fit."""
    problems = []
    for r in rows:
        s = summary[r["platform"]]
        clay = r["platform"] == "Clay"
        pairs = [
            ("briefs_written", D(r["briefs_written"]), D(s["accepted_rate_median"]) * 50),
            ("accuracy", D(r["accuracy"]), D(s["mean_accuracy_median"])),
            ("fabrications_of_20", D(r["fabrications_of_20"]), D(s["fabrications_median"])),
            ("status", r["status"], s["statuses"].split("=")[0]),
            ("steps", D(r["steps"]), D(s["steps_median"])),
            ("minutes", D(r["minutes"]), D(s["wallclock_min_median"])),
            ("model_cost_usd", D(r["model_cost_usd"]), D(s["agent_cost_usd_median"])),
            ("credit_cost_usd", D(r["credit_cost_usd"]), D(r["data_credit_cost_usd"]) + D(r["action_credit_cost_usd"])),
            # One action credit per brief on Clay; action credits are a Clay unit.
            ("action_credit_cost_usd", D(r["action_credit_cost_usd"]),
             rnd(D(r["briefs_written"]) * D(str(prices["actions"])), "0.01") if clay else 0),
            ("fabrication_rate_ci", (r["fabrication_rate_ci_low"], r["fabrication_rate_ci_high"]),
             wilson(int(r["fabrications_of_20"]), 20)),
        ]
        if s["cost_per_1000_accepted_usd_median"]:  # blank for a run below the pass line
            per_run = D(s["cost_per_1000_accepted_usd_median"]) * D(r["briefs_written"]) / 1000
            pairs.append(("data_credit_cost_usd", D(r["data_credit_cost_usd"]), rnd(per_run, "0.01")))
        problems += [f"{r['platform']} {col}: t6-results.csv has {a}, expected {b}" for col, a, b in pairs if a != b]
        problems += [f"{r['platform']} {c}: {r[c]} is outside its interval" for c in SCORES
                     if not D(r[c + "_ci_low"]) <= D(r[c]) <= D(r[c + "_ci_high"])]
    return problems


def interval_claims_hold(rows):
    """What RESULTS.md says about the intervals: which gaps are clear (no overlap) and which are not."""
    clay, a, b = rows

    def clear(higher, lower, col):
        return D(higher[col + "_ci_low"]) > D(lower[col + "_ci_high"])

    return (clear(clay, a, "accuracy") and clear(clay, a, "specificity") and not clear(clay, a, "usefulness")
            and all(clear(a, b, c) for c in SCORES)
            and clay["fabrication_rate_ci_high"] == a["fabrication_rate_ci_high"]
            and D(b["fabrication_rate_ci_low"]) > D(clay["fabrication_rate_ci_high"]))


def sentences(rows, summary, prices, audit, run_ids):
    """(file, figures): the figures must appear in this order on one line of that file."""
    clay, a, b = rows
    first, second = audit  # the two human audit rounds
    agreement = [x for r in audit for x in (f"{r['agreed']} of {r['n']}", r["percent_agreement"] + "%")]
    agreed_cells = "| " + " | ".join(f"{r['agreed']} of {r['n']} ({r['percent_agreement']}%)" for r in audit) + " |"
    both = f"{first['fabrication_kappa']} in both rounds"
    data_credits, action_credits = clay_credits(clay, summary["Clay"], prices)
    unfinished = [str(50 - int(r["briefs_written"])) for r in (a, b)]

    def row(label, col, rows=rows):
        return [label, "| " + " | ".join(r[col] for r in rows) + " |"]

    def interval(r, col):
        return f"{rnd(r[col + '_ci_low'], '0.1')}–{rnd(r[col + '_ci_high'], '0.1')}"

    results = [
        agreement + [both, first["accuracy_weighted_kappa"], second["accuracy_weighted_kappa"]],
        ["Run ID", "| " + " | ".join(run_ids[r["platform"]] for r in rows) + " |"],
        row("Wall-clock minutes", "minutes"),
        [f"Clay from {clay['ai_first_pass_fabrications']} to {clay['fabrications_of_20']}"],
        [f"{data_credits} credits", f"${prices['data_credits']}", f"${clay['data_credit_cost_usd']}",
         f"{action_credits} action credits", f"${prices['actions']}", f"${clay['action_credit_cost_usd']}",
         f"${clay['credit_cost_usd']}"],
        [x for r in rows for x in (f"{r['steps']} steps", f"{rnd(r['minutes'], '0.1')} minutes")],
        [f"left {unfinished[0]} briefs", f"left {unfinished[1]} incomplete", f"{b['fabrications_of_20']} fabricated"],
        [f"Provider B's {b['fabrications_of_20']}", f"flagged {b['ai_fabrications']}", f"person {b['human_fabrications']}"],
        ["AI's ratings alone", f"{clay['ai_accuracy']}, {a['ai_accuracy']} and {b['ai_accuracy']}"],
        [interval(clay, "usefulness"), interval(a, "usefulness"), pct(clay["fabrication_rate_ci_high"]),
         f"{pct(b['fabrication_rate_ci_low'])}–{pct(b['fabrication_rate_ci_high'])}"],
    ]
    method = [
        agreement[:2], agreement[2:],
        ["Agreed, as defined above", agreed_cells],
        row("Kappa on the fabrication call", "fabrication_kappa", audit),
        row("Linearly weighted kappa on accuracy", "accuracy_weighted_kappa", audit),
        [f"AI flagged {first['ai_flagged']}", f"person {first['human_flagged']}",
         f"person flagged {second['human_flagged']}", f"AI {second['ai_flagged']}"],
        ["Published:** accuracy"] + [" / ".join(r[c] for c in SCORES) for r in rows],
        row("Published:** briefs with a fabricated fact", "fabrications_of_20"),
        ["AI second pass only, 20 briefs"] + [" / ".join(r["ai_" + c] for c in SCORES) for r in rows],
        row("AI second pass only: briefs flagged", "ai_fabrications"),
        row("Person only, 3 briefs: accuracy", "human_accuracy"),
        row("Person only: briefs flagged", "human_fabrications"),
        row("AI first pass, 20 briefs: accuracy", "ai_first_pass_accuracy"),
        row("AI first pass: briefs flagged", "ai_first_pass_fabrications"),
        [f"each left {unfinished[0]} briefs"],
        [f"${prices['actions']} each"],
    ]
    harbor = [["{}, {} and {}".format(*(r["briefs_written"] for r in rows))]]
    return ([("RESULTS.md", f) for f in results] + [("METHODOLOGY.md", f) for f in method]
            + [("harbor/README.md", f) for f in harbor] + [("README.md", agreement[1::2])])


def has_figures(text, figures):
    # A figure must not run on into more digits: "29 steps" is not found in "129 steps", nor "$0.2" in "$0.26".
    return re.search(".*".join(r"(?<![\d.])" + re.escape(x) + r"(?!\.?\d)" for x in figures), text)


def with_block(text, name, body):
    """text with the generated block `name` set to body, or None if the file has no such block."""
    start, end = f"<!-- generated:{name} -->\n", "\n<!-- /generated -->"
    head, found_start, rest = text.partition(start)
    _, found_end, tail = rest.partition(end)
    return head + start + body + end + tail if found_start and found_end else None


def main():
    rows = read_csv("t6-results.csv")
    summary = {s["platform_label"]: s for s in read_csv("summary.csv")}
    prices = json.loads((REPO / "config" / "bench.json").read_text(encoding="utf-8"))["platforms"]["clay"]["unit_prices"]
    problems = check_csv(rows, summary, prices)
    audit = read_csv("audit-agreement.csv")  # kappa itself needs the private ratings: scripts/review_stats.py
    problems += [f"audit-agreement.csv round {r['round']}: {r['agreed']} of {r['n']} is not {r['percent_agreement']}%"
                 for r in audit if pct(D(r["agreed"]) / D(r["n"])) != r["percent_agreement"] + "%"]
    manifest = json.loads((REPO / "results" / "manifest-t6.json").read_text(encoding="utf-8"))
    run_ids = {r["platform"]: r["run_id"] for r in manifest["runs"]}
    texts = {}

    def text(name):
        return texts.setdefault(name, (REPO / name).read_text(encoding="utf-8"))

    headers = {"t6-results.csv": rows[0], "summary.csv": next(iter(summary.values())), "audit-agreement.csv": audit[0]}
    for name, header in headers.items():
        section = text("docs/DATA-DICTIONARY.md").partition(f"## `results/{name}`")[2].partition("\n## ")[0]
        problems += [f"docs/DATA-DICTIONARY.md: `{col}` of results/{name} is not described"
                     for col in header if f"`{col}`" not in section]

    for name, file, body in (("results-table", "RESULTS.md", table(rows)), ("headline", "README.md", headline(rows))):
        new = with_block(text(file), name, body or "")
        if body is None:
            problems.append("README.md headline no longer holds (Clay most accurate, all 50 written, lowest credit cost)")
        elif new is None:
            problems.append(f"{file}: no <!-- generated:{name} --> ... <!-- /generated --> block")
        elif new != text(file) and "--write" in sys.argv:
            (REPO / file).write_text(new, encoding="utf-8")
            texts[file] = new
            print(f"{file}: {name} rewritten")
        elif new != text(file):
            diff = difflib.unified_diff(text(file).splitlines(), new.splitlines(), file, "from results/t6-results.csv", lineterm="")
            problems.append(f"{file}: {name} is stale; run with --write:\n" + "\n".join(diff))

    if not interval_claims_hold(rows):
        problems.append("RESULTS.md: the paragraph on which gaps are clear no longer matches the intervals; rewrite it "
                        "and interval_claims_hold")
    if audit[0]["fabrication_kappa"] != audit[1]["fabrication_kappa"]:
        problems.append('RESULTS.md: the fabrication kappa is no longer the same "in both rounds"; rewrite the sentence '
                        "and `sentences`")
    if rows[1]["briefs_written"] != rows[2]["briefs_written"]:
        problems.append('METHODOLOGY.md: Provider A and Provider B no longer "each left" the same number of briefs; '
                        "rewrite the sentence and `sentences`")
    problems += [f"{file}: no line has these figures from the results files, in this order: " + "; ".join(figures)
                 for file, figures in sentences(rows, summary, prices, audit, run_ids)
                 if not has_figures(text(file), figures)]

    if problems:
        print("\n".join(problems))
        return 1
    print("Published numbers match results/t6-results.csv, results/summary.csv and results/audit-agreement.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
