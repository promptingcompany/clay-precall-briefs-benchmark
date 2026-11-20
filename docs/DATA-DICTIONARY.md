# Data dictionary

Every column of the three CSV files in `results/`. [RESULTS.md](../RESULTS.md) shows the numbers and [METHODOLOGY.md](../METHODOLOGY.md) says how the benchmark was run and scored. `scripts/check_results.py` fails if a column in one of the files is missing from this page.

A blank cell means "not available", never zero. Three sources come up again and again:

- **`score_t6`** is the scorer in `scoring/scorers.py`.
- **`benchkit`** is the harness that ran the agents and wrote `summary.csv` (`./bench summary`).
- **`scripts/review_stats.py`** computes figures from the per-brief ratings. The ratings are private (README, "Data on request"), so those columns can't be recomputed from this repository alone.

## `results/t6-results.csv`

One row per platform. Every number in the results table comes from this file.

| Column | Meaning | Unit | How it is computed |
|---|---|---|---|
| `platform` | The platform as published: Clay, Provider A or Provider B | Text | The platform's label in `config/bench.json` |
| `briefs_written` | Briefs with all five output columns filled | Count, of 50 | `score_t6` counts the filled rows. Equals `accepted_rate_median` × 50 in `summary.csv` |
| `accuracy` | Average accuracy rating: are the stated facts true per public sources | Score, 1–5 | `score_t6`: the mean of all 23 ratings in the run's review file (the AI's 20 and the person's 3), to 2 decimals. Equals `mean_accuracy_median` in `summary.csv` |
| `specificity` | Average specificity rating: specific to this company, not generic | Score, 1–5 | `score_t6`, as for `accuracy`. Read from the private run record and checked by `scripts/review_stats.py` |
| `usefulness` | Average usefulness rating: would an account executive use it on a call | Score, 1–5 | `score_t6`, as for `specificity` |
| `fabrications_of_20` | Reviewed briefs in which either rater flagged a fabricated fact | Count, of 20 | `score_t6`: a brief counts once if any rater said yes. Equals `fabrications_median` in `summary.csv` |
| `status` | Pass, or Partial for a run below the pass line | Text | `score_t6` proposes it from the pass line (all 50 written, accuracy at least 3.5, at most 1 fabrication); recorded on the run. Matches `statuses` in `summary.csv` |
| `steps` | The agent's tool calls | Count | `benchkit` counts them in the agent's transcript. Equals `steps_median` in `summary.csv` |
| `minutes` | Wall-clock time of the run | Minutes | `benchkit`: the run's stop time minus its start time, to 2 decimals. Equals `wallclock_min_median` in `summary.csv` |
| `data_credit_cost_usd` | Cost of the platform credits the run used. For Clay, data credits only | US dollars | The drop in the credit balance × the list price per credit. Clay: `cost_per_1000_accepted_usd_median` × 50 ÷ 1,000, rounded to the cent. Provider A and B: from the private run records, because their prices are not published |
| `action_credit_cost_usd` | Cost of Clay's action credits. 0 for the other platforms, because actions are a Clay unit | US dollars | 50 action credits, one per brief, read by hand from the run's log × the price per action in `config/bench.json` |
| `credit_cost_usd` | Platform credit cost of the run | US dollars | `data_credit_cost_usd` + `action_credit_cost_usd` |
| `model_cost_usd` | What the agent's own model calls cost. Billed separately, never added to the platform cost | US dollars | Reported by Claude Code at the end of the run and saved by `benchkit`. Equals `agent_cost_usd_median` in `summary.csv` |
| `accuracy_ci_low`, `accuracy_ci_high` | The two ends of the 95% interval for `accuracy` | Score, 1–5 | `scripts/review_stats.py`: percentile bootstrap of the mean. The 23 ratings are resampled with replacement 10,000 times (seed 20261119); the ends are the 2.5th and 97.5th percentiles of the resampled means |
| `specificity_ci_low`, `specificity_ci_high` | The same for `specificity` | Score, 1–5 | As for `accuracy_ci_low` |
| `usefulness_ci_low`, `usefulness_ci_high` | The same for `usefulness` | Score, 1–5 | As for `accuracy_ci_low` |
| `fabrication_rate_ci_low`, `fabrication_rate_ci_high` | The two ends of the 95% interval for the share of reviewed briefs with a fabricated fact | Share, 0–1 | Wilson score interval for `fabrications_of_20` out of 20 (`wilson` in `scripts/check_results.py`). CI recomputes it |
| `ai_accuracy`, `ai_specificity`, `ai_usefulness` | Average ratings from the AI reviewer's second pass alone | Score, 1–5 | `scripts/review_stats.py`: the mean of the AI's 20 ratings, to 2 decimals |
| `ai_fabrications` | Briefs the AI's second pass flagged as fabricated | Count, of 20 | `scripts/review_stats.py` |
| `human_accuracy` | Average accuracy from the person's ratings alone (audit round 2) | Score, 1–5 | `scripts/review_stats.py`: the mean of the person's 3 ratings, to 2 decimals |
| `human_fabrications` | Briefs the person flagged as fabricated (audit round 2) | Count, of 3 | `scripts/review_stats.py` |
| `ai_first_pass_accuracy` | Average accuracy from the AI's first pass, before the reviewer's rules were clarified | Score, 1–5 | `scripts/review_stats.py`: the mean of the first pass's 20 ratings, to 2 decimals |
| `ai_first_pass_fabrications` | Briefs the AI's first pass flagged as fabricated | Count, of 20 | `scripts/review_stats.py` |

## `results/summary.csv`

One row per platform, written by `benchkit` (`./bench summary`) from the run records. The harness is built for several runs per platform, so most measures come as a median, a minimum and a maximum. Here there is one run per platform, so all three are that run's value. Each is rounded to 2 decimals.

| Column | Meaning | Unit | How it is computed |
|---|---|---|---|
| `task_id` | The task's ID | Text (`T6`) | From the run record; the ID in `config/bench.json` |
| `task_version` | The version of the task spec the run used | Text (`T6-v1`) | From the run record |
| `platform_label` | The platform as published: Clay, Provider A or Provider B | Text | The platform's label in `config/bench.json` |
| `executor` | Who did the task. `agent` means an AI agent | Text | From the run record |
| `operator_profile` | The kind of operator. `agent` for every run here | Text | From the run record |
| `cost_runs` | Runs whose usage counts towards cost | Count | `benchkit` summary: the first run with recorded usage for each task version, platform and account |
| `runs` | Runs in the row | Count | `benchkit` summary |
| `ranked_runs` | Runs that ended as Pass, Partial, Fail or Did not finish | Count | `benchkit` summary |
| `statuses` | How many runs ended in each status, for example `Pass=1` | Text | `benchkit` summary, from each run's status ([METHODOLOGY.md](../METHODOLOGY.md) section 4) |
| `environment_labels` | The pricing basis the run was labelled with | Text (`self-serve monthly`) | Given when the run was started (`--env`) |
| `steps_median`, `steps_min`, `steps_max` | The agent's tool calls | Count | `benchkit` counts them in the agent's transcript |
| `active_min_median`, `active_min_min`, `active_min_max` | Time the agent process ran | Minutes | `benchkit` times the agent process |
| `wallclock_min_median`, `wallclock_min_min`, `wallclock_min_max` | Wall-clock time of the run | Minutes | `benchkit`: the run's stop time minus its start time |
| `accepted_rate_median`, `accepted_rate_min`, `accepted_rate_max` | Share of the 50 briefs with all five output columns filled | Share, 0–1 | `score_t6`: filled rows ÷ 50 |
| `cost_per_accepted_record_usd_median`, `cost_per_accepted_record_usd_min`, `cost_per_accepted_record_usd_max` | Platform usage cost per accepted brief. Blank for a run below the pass line, where no brief counts as accepted. For Clay it covers data credits only. Rounded to the cent, so use the per-1,000 columns for exact work | US dollars per brief | `benchkit`: units used × list price per unit ÷ accepted briefs |
| `cost_per_1000_accepted_usd_median`, `cost_per_1000_accepted_usd_min`, `cost_per_1000_accepted_usd_max` | The same cost per 1,000 accepted briefs. Blank for a run below the pass line | US dollars per 1,000 briefs | `benchkit`: cost per accepted brief × 1,000 |
| `agent_cost_usd_median`, `agent_cost_usd_min`, `agent_cost_usd_max` | What the agent's own model calls cost | US dollars | Reported by Claude Code at the end of the run and saved by `benchkit` |
| `price_effective_date` | The date the list prices were read | Date, YYYY-MM-DD | `price_effective_date` in `config/bench.json` |
| `mean_accuracy_median` | Average accuracy rating of the run's reviewed briefs | Score, 1–5 | `score_t6`: the mean of all 23 ratings in the run's review file, to 2 decimals |
| `fabrications_median` | Reviewed briefs in which either rater flagged a fabricated fact | Count, of 20 | `score_t6`: a brief counts once if any rater said yes |

## `results/audit-agreement.csv`

One row per human audit round. In round 1 the person's ratings are set against the AI's first pass; in round 2, against its second pass. Every figure is computed by `scripts/review_stats.py` from the private audit sheets. The samples are small (12 and 9 briefs), so the kappa values are rough ([METHODOLOGY.md](../METHODOLOGY.md) section 7).

| Column | Meaning | Unit | How it is computed |
|---|---|---|---|
| `round` | The audit round | Number (1 or 2) | The audit sheet's round number |
| `n` | Briefs the person rated in the round | Count | Rows in the audit sheet |
| `agreed` | Briefs on which the person and the AI agreed: within 1 point on each of the three scores, and the same fabrication call | Count, of `n` | `agree` in `scripts/review_audit.py`, counted by `scripts/review_stats.py` |
| `percent_agreement` | `agreed` as a share of `n` | Percent, whole number | `agreed` ÷ `n` × 100. CI recomputes it |
| `ai_flagged` | Briefs in the round the AI flagged as fabricated | Count, of `n` | `scripts/review_stats.py` |
| `human_flagged` | Briefs in the round the person flagged as fabricated | Count, of `n` | `scripts/review_stats.py` |
| `fabrication_kappa` | Cohen's kappa on the fabrication call (yes or no): agreement corrected for the agreement expected by chance | −1 to 1: 0 = chance, 1 = perfect. Blank if undefined | `kappa` in `scripts/review_stats.py`: (agreement seen − agreement expected by chance) ÷ (1 − agreement expected by chance). Chance comes from how often each rater said yes and no |
| `accuracy_weighted_kappa` | Linearly weighted Cohen's kappa on the accuracy score: near misses get partial credit | −1 to 1: 0 = chance, 1 = perfect. Blank if undefined | `kappa` in `scripts/review_stats.py`, where two scores agree by 1 − (their difference ÷ 4) |
