# Reproductions

A log of attempts to reproduce this benchmark's results, ours and anyone else's. To add yours, open an issue with the **Reproduction report** template. We add a row whether or not it matched.

| Date | Who | What was tried | Result | Link |
|---|---|---|---|---|
| 2026-11-19 | The Prompting Company | Offline re-score. The steps of `scripts/reproduce.sh` on the three private run folders: the scorer and the interval script were run again on the saved outputs and ratings. No new agent run and no new review. The harness came from a local checkout (v0.1.3), not a fresh install | Matched: every column of `results/summary.csv`, and every review figure and interval in `results/t6-results.csv` | [scripts/reproduce.sh](../scripts/reproduce.sh) |
| 2026-11-19 | The Prompting Company | Harbor setup check, with API-key-only Clay access (narrower than the original run). One run of the Clay task in a container, with the API key and saved routine IDs in place of the signed-in Clay CLI, graded by the AI reviewer alone | Not comparable to the published result. It wrote 46 of 50 briefs and scored 3.85 for accuracy. A repeat under the original access is pending | [harbor/README.md](../harbor/README.md#checked-against-our-runs) |

Both rows are ours, so neither is an independent reproduction.
