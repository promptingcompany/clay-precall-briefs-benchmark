#!/usr/bin/env bash
# Re-check everything a clone can check: the tests, the published numbers, and that the results contain no email addresses.
# With the private files (README, "Data on request") it also checks the three runs against the published hashes,
# re-scores them and compares them with the published results.   Usage: scripts/reproduce.sh [private_dir]   (default: private/ in this repository)
set -euo pipefail
private=${1:-"$(dirname "$0")/../private"}
[ ! -d "$private" ] || private=$(cd "$private" && pwd)
cd "$(dirname "$0")/.."

[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install --quiet -r requirements.txt
export PATH="$PWD/.venv/bin:$PATH"

python -I -m unittest discover -s tests
python scripts/check_results.py
./bench check-anon

if [ ! -d "$private/runs" ]; then
  echo "No run folders at $private/runs: skipped re-scoring the runs (README, \"Data on request\")."
  exit 0
fi

# Score copies of the three runs, so the folders you were sent stay as they were hashed in results/manifest-t6.json.
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/private/runs" "$tmp/results"
ids=$(python -c "import json; print(*[r['run_id'] for r in json.load(open('results/manifest-t6.json'))['runs']])")
for id in $ids; do cp -R "$private/runs/$id" "$tmp/private/runs/"; done
# Before re-scoring: every file in the three run folders must match its published hash.
cp results/manifest-t6.json "$tmp/results/manifest.json"
BENCH_ROOT="$tmp" ./bench audit
for id in $ids; do BENCH_ROOT="$tmp" ./bench score "$id" >/dev/null; done
BENCH_ROOT="$tmp" ./bench summary >/dev/null
python - "$tmp/results/summary.csv" <<'EOF'
import csv
import sys


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {r["platform_label"]: r for r in csv.DictReader(f)}


fresh, published = rows(sys.argv[1]), rows("results/summary.csv")
diffs = [f"{label} {col}: published {value!r}, re-scored {fresh[label].get(col)!r}"
         for label, row in published.items() for col, value in row.items() if fresh[label].get(col) != value]
print("\n".join(diffs) if diffs else "Re-scored runs match results/summary.csv")
sys.exit(1 if diffs else 0)
EOF
python scripts/review_stats.py "$private"
