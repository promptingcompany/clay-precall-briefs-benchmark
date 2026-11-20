"""Acceptance test for T6 (tasks/precall-briefs.md), loaded by benchkit. `score_t6` is the seven-task study's function,
unchanged since its pre-registration tag (docs/PREREG.md). It returns metrics, accepted_records, records_in,
floor_met and a proposed status."""
import statistics

from benchkit.runs import run_dir
from benchkit.scoring import YES, check_columns, output_csv, rate, read_csv


def score_t6(run, cfg):
    t = cfg["tasks"]["T6"]
    header, rows = output_csv(run)
    check_columns(header, t["output_columns"])
    filled = sum(all((r[c] or "").strip() for c in t["output_columns"]) for r in rows)
    _, scores = read_csv(run_dir(run["run_id"]) / "review" / "t6-scores.csv")
    by_item = {}
    for s in scores:
        by_item.setdefault(s["domain"], []).append(s)
    disagreements = sum(
        1 for items in by_item.values() for k in ("accuracy", "specificity", "usefulness")
        if len(items) > 1 and max(float(i[k]) for i in items) - min(float(i[k]) for i in items) > 1
    )

    def mean(k):
        return round(statistics.mean(float(s[k]) for s in scores), 2) if scores else None

    fabrications = sum(1 for items in by_item.values() if any((i["fabricated"] or "").lower() in YES for i in items))
    f = t["floor"]
    acc = mean("accuracy")
    floor = filled == t["rows"] and acc is not None and acc >= f["mean_accuracy"] and fabrications <= f["max_fabrications"]
    return {
        "records_in": t["rows"], "accepted_records": filled if floor else 0, "accepted_rate": rate(filled, t["rows"]),
        "metrics": {"rows_filled": filled, "reviewed_items": len(by_item), "mean_accuracy": acc,
                    "mean_specificity": mean("specificity"), "mean_usefulness": mean("usefulness"),
                    "fabrications": fabrications, "reviewer_disagreements_over_1pt": disagreements},
        "floor_met": floor, "proposed_status": "Pass" if floor else ("Partial" if filled else "Fail"),
    }


SCORERS = {"T6": score_t6}


def output_contacts(run, cfg):
    """Emails and phones for benchkit's verifier step: a brief has none."""
    return [], []
