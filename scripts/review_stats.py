#!/usr/bin/env python3
"""The figures that come from the private per-brief ratings: in results/t6-results.csv, the review scores, their 95%
intervals, and the AI-only, person-only and first-pass columns; and all of results/audit-agreement.csv (how often the
person and the AI agreed in each audit round, and Cohen's kappa).

    python scripts/review_stats.py [private_dir]           # exit 1 and show what differs from the CSVs
    python scripts/review_stats.py [private_dir] --write   # rewrite those columns, and audit-agreement.csv

private_dir (default: private/) holds runs/<run_id>/review/t6-scores.csv for the three runs in
results/manifest-t6.json, and in review/: T6-blind-ai-r1.csv with T6-blind-key.json for the AI's first pass,
T6-blind-ai.csv for its second, and the person's audit sheets T6-audit-r1.csv and T6-audit-r2.csv.
The ratings are not published (README, "Data on request"); this script is how the committed figures were made.
"""
import csv
import json
import random
import statistics
import sys
from fractions import Fraction
from pathlib import Path

from check_results import REPO, SCORES, read_csv, rnd, wilson
from review_audit import agree, flag

SEED, RESAMPLES = 20261119, 10_000
AUDITS = {1: "T6-blind-ai-r1.csv", 2: "T6-blind-ai.csv"}  # audit round -> the AI pass the person audited


def rows_of(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def interval(values):
    """95% percentile bootstrap of the mean: RESAMPLES resamples of the ratings, with replacement, from a fixed seed."""
    rng = random.Random(SEED)
    means = [statistics.fmean(rng.choices(values, k=len(values))) for _ in range(RESAMPLES)]
    cuts = statistics.quantiles(means, n=40, method="inclusive")  # cut points every 2.5%
    return cuts[0], cuts[-1]


def mean(rows, col):
    return str(rnd(statistics.fmean(float(r[col]) for r in rows), "0.01"))


def flagged(rows):
    """Briefs any rater flagged as fabricated, counted once each."""
    return len({r["domain"] for r in rows if flag(r)})


def stats(private, run_id):
    scores = rows_of(private / "runs" / run_id / "review" / "t6-scores.csv")
    ai = [r for r in scores if r["reviewer"] == "ai"]
    human = [r for r in scores if r["reviewer"] != "ai"]
    key = json.loads((private / "review" / "T6-blind-key.json").read_text(encoding="utf-8"))
    first = [r for r in rows_of(private / "review" / "T6-blind-ai-r1.csv") if key[r["item_id"]] == run_id]
    briefs = len({r["domain"] for r in scores})
    out = {col: mean(scores, col) for col in SCORES} | {"fabrications_of_20": str(flagged(scores))}
    for col in SCORES:
        low, high = interval([float(r[col]) for r in scores])
        out |= {col + "_ci_low": str(rnd(low, "0.01")), col + "_ci_high": str(rnd(high, "0.01"))}
    out["fabrication_rate_ci_low"], out["fabrication_rate_ci_high"] = wilson(flagged(scores), briefs)
    return out | {"ai_" + col: mean(ai, col) for col in SCORES} | {
        "ai_fabrications": str(flagged(ai)), "human_accuracy": mean(human, "accuracy"),
        "human_fabrications": str(flagged(human)), "ai_first_pass_accuracy": mean(first, "accuracy"),
        "ai_first_pass_fabrications": str(flagged(first))}


def kappa(pairs, weight):
    """Cohen's kappa for two raters' ratings of the same items: (agreement seen - agreement expected by chance) /
    (1 - agreement expected by chance), so 0 is chance and 1 is perfect. weight(a, b) is 1 when two ratings agree fully
    and 0 when not at all. Chance is every rating by one rater set against every rating by the other.
    None if chance agreement is already complete (both raters gave one same rating throughout): kappa is undefined."""
    n = len(pairs)
    seen = Fraction(sum(weight(a, b) for a, b in pairs), n)
    chance = Fraction(sum(weight(a, b) for a, _ in pairs for _, b in pairs), n * n)
    return None if chance == 1 else (seen - chance) / (1 - chance)


def audit(private):
    """One row per human audit round. "Agreed" (review_audit.agree) has two parts, so each gets its own kappa: plain
    kappa on the fabrication call, and linearly weighted kappa on the 1-5 accuracy score (1 point apart is 3/4 agreement)."""
    def show(k):
        return "" if k is None else str(rnd(float(k), "0.01"))

    out = []
    for number, ai_file in AUDITS.items():
        ai = {r["item_id"]: r for r in rows_of(private / "review" / ai_file)}
        pairs = [(ai[h["item_id"]], h) for h in rows_of(private / "review" / f"T6-audit-r{number}.csv")]
        agreed = sum(agree(a, h) for a, h in pairs)
        out.append({
            "round": str(number), "n": str(len(pairs)), "agreed": str(agreed),
            "percent_agreement": str(rnd(100 * agreed / len(pairs), "1")),
            "ai_flagged": str(sum(flag(a) for a, _ in pairs)), "human_flagged": str(sum(flag(h) for _, h in pairs)),
            "fabrication_kappa": show(kappa([(flag(a), flag(h)) for a, h in pairs], lambda a, b: a == b)),
            "accuracy_weighted_kappa": show(kappa([(int(a["accuracy"]), int(h["accuracy"])) for a, h in pairs],
                                                  lambda a, b: 1 - Fraction(abs(a - b), 4)))})
    return out


def differences(name, rows):
    """What results/<name> would need changing to hold rows. The first column names a row: the platform, or the round."""
    old = {next(iter(r.values())): r for r in (read_csv(name) if (REPO / "results" / name).exists() else [])}
    return [f"{name} {label} {col}: the file has {old.get(label, {}).get(col)}, the ratings give {value}"
            for label, row in ((next(iter(r.values())), r) for r in rows)
            for col, value in row.items() if old.get(label, {}).get(col) != value]


def main():
    args = [a for a in sys.argv[1:] if a != "--write"]
    private = Path(args[0]) if args else REPO / "private"
    manifest = json.loads((REPO / "results" / "manifest-t6.json").read_text(encoding="utf-8"))
    run_of = {r["platform"]: r["run_id"] for r in manifest["runs"]}
    new = {"t6-results.csv": [r | stats(private, run_of[r["platform"]]) for r in read_csv("t6-results.csv")],
           "audit-agreement.csv": audit(private)}
    diffs = {name: d for name, rows in new.items() if (d := differences(name, rows))}
    if diffs and "--write" in sys.argv:
        for name in diffs:
            with open(REPO / "results" / name, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, list(new[name][0]), lineterminator="\n")
                w.writeheader()
                w.writerows(new[name])
            print(f"results/{name} rewritten; now run scripts/check_results.py --write")
        return 0
    print("\n".join(d for ds in diffs.values() for d in ds)
          or "results/t6-results.csv and results/audit-agreement.csv match the per-brief ratings")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
