# write-precall-briefs

The pre-call briefs task (ID T6-v1, [tasks/precall-briefs.md](../../tasks/precall-briefs.md)) as a [Harbor](https://harborframework.com/docs) task: write a 3-bullet pre-call brief and an opening line for 50 accounts. How to run it, how to get the accounts file, how grading works and how it differs from our runs are in [harbor/README.md](../README.md).

Specific to this task:

- `instruction.md` is the exact prompt the benchmark agents received, plus one environment note (Clay's API and saved routines).
- `tests/grade.py` applies the same rules as `scoring/scorers.py`. `reward` is the share of the 50 briefs that are filled; `passed` is 1 at the pass line.
- The accounts file goes in `environment/` for the agent and in `tests/` for the grader.
- The grader needs `ANTHROPIC_API_KEY`. Each run spends real platform credits; [RESULTS.md](../../RESULTS.md) has what ours cost.
