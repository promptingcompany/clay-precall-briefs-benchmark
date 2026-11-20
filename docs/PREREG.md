# Pre-registration record

This task was pre-registered as part of a seven-task study by The Prompting Company. The study's method, task specs, scoring code and config were frozen before any counted run, in commit `c4a733fede1feac77729e7da6053b770b5e9d28e` (tag `v1.0-prereg`, 2026-11-06T19:51:17-08:00). The three runs reported here started on 2026-11-09 and 2026-11-10 (UTC).

That commit is kept in a private archive of the study. To check that the method was frozen before the runs, open an issue titled "Pre-registration check" on this repository and we'll give you read access. Then compare each frozen file with its SHA-256 below (`git show v1.0-prereg:<file> | shasum -a 256`).

## Frozen files that govern this task

| File at `v1.0-prereg` in the study | SHA-256 |
|---|---|
| `METHODOLOGY.md` | `8c3a6fcb1575df8b7d891140c738fc43fec227b4c92ab5e05ad5326a701b71a5` |
| `tasks/T6.md` (now `tasks/precall-briefs.md`) | `5d40b046f84eea8806881d9839a2c3b1ebfbc634ab3daa5280baa9a8c38863b3` |
| `config/bench.json` | `0f52aa252e2b4080d48aa0c1c8c38f23f652c38aebe27ffa470c3d82b77200bc` |
| `scoring/scorers.py` | `1e5ad5c3a288ac224c8826ec406de10c547decf8d5725251ecb3a037d7a791d1` |

All three runs used the same input file, `t6-accounts.csv`, SHA-256 `9f8bbf3e70ac2ee51354fe88afc148f5c225f11d3d6cbf144d36d3b206b50cb3` (from the study's run plan and each run record).

## How the files here differ from the frozen ones

The files in this repository are cut down to one task, so their hashes won't match the table.

- **`config/bench.json` is not the frozen config.** The frozen config lives in the study. This one keeps only this task and the three platforms, and its title and agent task list name only this task. The task's prompt, output columns, pass line and review settings, the agent's model, tools and limits, the agent rules and Clay's prices are unchanged. Removed: the other tasks, the plan tiers only they used, the email-verifier settings, the held-out-rows setting and the monthly-cost scenario's record count. Three notes are reworded: Clay's price note and the two disclosure notes. `scenario.projection_task` is set to null, because the study projected that scenario from another task. `verifier.email_api_env` stays only so the harness strips that key from the agent's environment; this task verifies no emails.
- **`scoring/scorers.py`** holds only this task's scorer. The `score_t6` function is the same, character for character, as at the tag.
- **`tasks/precall-briefs.md`** (frozen as `tasks/T6.md`) is the study's current file, renamed here; the title line drops "T6:". It differs from the frozen text in wording only: "draft;" removed from the version line; the input path reads `private/datasets/`; "(proposed)" removed from the quality floor heading; and the Provider A and B platform notes say their tier names and product notes are not published (Provider A's tier no longer reads "Tier 1 (quote)"); the version line no longer gives the old path; and two dated editorial notes are added (how the study's tasks were chosen, and that walkthrough timings were not run).
- **`METHODOLOGY.md`** is a cut of the study's method for this task, with an account of the review as it was done.

What changed in the method itself after the freeze is in [CHANGELOG.md](CHANGELOG.md).
