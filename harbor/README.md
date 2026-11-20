# Harbor task

The benchmark's task as a [Harbor](https://harborframework.com/docs) task, so anyone can rerun the Clay side with one command. [write-precall-briefs](write-precall-briefs) asks the agent to write a pre-call brief and an opening line for 50 accounts. Its `instruction.md` is the exact prompt our agents received plus one environment note (below), and its grader applies the same pass line as `scoring/scorers.py`.

## Quickstart

Have [Harbor](https://harborframework.com/docs), Docker, a Clay API key for a workspace with credits, and an Anthropic API key for the reviewer.

```bash
uv tool install --python 3.13 harbor
git clone https://github.com/promptingcompany/clay-precall-briefs-benchmark && cd clay-precall-briefs-benchmark
export CLAY_API_KEY=... ANTHROPIC_API_KEY=...
eval "$(harbor/clay-routine-env.sh)"   # loads your workspace's 19 Clay routine IDs; needs the clay CLI signed in
harbor run -p harbor/write-precall-briefs -a nop                                        # an agent that does nothing scores 0
harbor run -p harbor/write-precall-briefs -a claude-code -m anthropic/claude-opus-5-5   # the benchmark's agent and model
```

Each run spends real platform credits; [RESULTS.md](../RESULTS.md) has what ours cost.

## The accounts file

`t6-accounts.csv` names a contact at each account, so it is not in the repo. The [README](../README.md#data-on-request) says how to ask for it, and until when. Put one copy in `write-precall-briefs/environment/` and one in `write-precall-briefs/tests/` (both paths are gitignored). Without it the task still builds, and the grader reports `data_missing` instead of a score.

## How grading works

- **The grader runs in its own container** after the agent finishes (`environment_mode = "separate"`).
- **The briefs** are scored by the same AI reviewer and rubric as our runs (Claude Sonnet 5.5 with web search), on the same 20 accounts every time. Without `ANTHROPIC_API_KEY` the review is skipped and the task can't pass.
- **`reward`** is the share of the 50 briefs that are filled; **`passed`** is the pre-registered pass line ([METHODOLOGY.md](../METHODOLOGY.md) section 4).

## Checked against our runs

On our three runs' outputs the grader counts the same filled briefs as the scorer (50, 46 and 46). The review scores depend on a fresh AI review, so they vary by a few points between runs.

**Harbor setup check (2026-11-19).** One run with API-key-only Clay access, which is narrower than the original run's signed-in Clay CLI (see Clay access below). It is not comparable to the published result; a repeat under the original access is pending. It is logged in [REPRODUCTIONS.md](../docs/REPRODUCTIONS.md).

## Differences from our runs

- **Clay access.** Our agent ran on a laptop where the Clay CLI was signed in through the browser, which grants more than the API key alone (tables, workflows, listing routines). A Harbor container has only the key, so the task passes in your workspace's saved routine IDs (`harbor/clay-routine-env.sh`), and the instruction ends with one note saying so and asking the agent to save its output as it goes. Our original run built a Clay workflow, which the key alone can't do.
- **Review sample.** The grader reviews the first 20 accounts by a hash of the domain. Ours were 20 drawn by the blind sampler, so they are not the same 20 accounts.
- **One reviewer.** The grader uses the AI reviewer alone; our published scores also average in a person's ratings of 3 accounts ([METHODOLOGY.md](../METHODOLOGY.md) section 7).
- **Clay only.** The two competitors are anonymized; a task for another vendor needs your own credentials and the vendor's name in the instruction.
