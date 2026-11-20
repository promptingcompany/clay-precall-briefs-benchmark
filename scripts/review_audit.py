"""Human audit of the AI review of T6.

make:  python3 scripts/review_audit.py make T6   -> private/review/T6-audit-r<N>.csv (next round): a blank sheet for 20%
       of the accounts not audited before, whole accounts so every platform is audited on the same ones.
merge: python3 scripts/review_audit.py merge T6  -> prints human-vs-AI agreement for the latest round and writes
       private/review/T6-final.csv for `bench blind-import`: the AI rows plus that round's human rows (two raters).
"""
import csv
import random
import sys
from pathlib import Path

REVIEW = Path(__file__).resolve().parent.parent / "private" / "review"
COLS = ["accuracy", "specificity", "usefulness", "fabricated"]
SHARE = 0.2
YES = {"y", "yes", "true", "1"}  # as benchkit.scoring.YES


def read(name):
    with open(REVIEW / name, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        return rd.fieldnames, list(rd)


def write(name, header, rows):
    with open(REVIEW / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, header, extrasaction="ignore")  # reviewer's extra columns (notes) stay in the audit file
        w.writeheader()
        w.writerows(rows)


def rounds(task):
    return sorted(REVIEW.glob(f"{task}-audit-r*.csv"), key=lambda p: int(p.stem.rsplit("-r", 1)[1]))


def make(task):
    header, rows = read(f"{task}-blind.csv")
    earlier = rounds(task)  # audit fresh accounts only
    seen = {r["item_id"] for p in earlier for r in read(p.name)[1]}
    seen_doms = {r["domain"] for r in rows if r["item_id"] in seen}
    rows = [r for r in rows if r["domain"] not in seen_doms]
    rng = random.Random(f"audit-{task}-r{len(earlier) + 1}")
    doms = sorted({r["domain"] for r in rows})
    pick = set(rng.sample(doms, max(1, round(len(doms) * SHARE))))
    chosen = [r for r in rows if r["domain"] in pick]
    rng.shuffle(chosen)
    for r in chosen:
        r.update({c: "" for c in COLS})
        r["reviewer"] = "human"
    name = f"{task}-audit-r{len(earlier) + 1}.csv"
    write(name, header, chosen)
    print(f"{task}: {len(chosen)} rows to audit -> {REVIEW / name}")


def flag(r):
    return r["fabricated"].strip().lower() in YES


def agree(a, h):
    """Within 1 point on each score, and the same fabrication call."""
    return all(abs(int(a[c]) - int(h[c])) <= 1 for c in COLS[:3]) and flag(a) == flag(h)


def merge(task):
    header, ai = read(f"{task}-blind-ai.csv")
    ai_by = {r["item_id"]: r for r in ai}
    latest = rounds(task)[-1]  # earlier rounds were rated under older rules, against an earlier AI pass
    human = [h for h in read(latest.name)[1] if all(h[c].strip() for c in COLS)]
    if not human:
        sys.exit(f"{task}: no filled audit rows in {latest.name}")
    ok = sum(agree(ai_by[h["item_id"]], h) for h in human)
    print(f"{task} {latest.name}: {len(human)} rows, agreement with AI {ok}/{len(human)}")
    write(f"{task}-final.csv", header, ai + human)
    print(f"{task}: {len(human)} human ratings added -> import with: "
          f"./bench blind-import --task {task} --file private/review/{task}-final.csv")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("make", "merge") or sys.argv[2] != "T6":
        sys.exit(__doc__ + "\nusage: python3 scripts/review_audit.py <make|merge> T6")
    {"make": make, "merge": merge}[sys.argv[1]](sys.argv[2])
