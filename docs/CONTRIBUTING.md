# Contributing

This repository holds one task of a pre-registered benchmark, so contributions work differently from a normal codebase.

## Reporting an error in the results or scoring

Open an issue with the **Results or scoring error** template. Include the `RESULTS.md` table row or the `results/` CSV cell, what you believe is wrong, and how you checked (a command, a source URL, or a line of scoring code). Confirmed errors are fixed in the open: the correction goes in `CHANGELOG.md` with a date and, if a score changes, the results files are corrected, the `RESULTS.md` table is rewritten from them (`python scripts/check_results.py --write`) and re-dated.

## Security problems and data concerns

Don't open an issue. Follow [SECURITY.md](../SECURITY.md).

## Changes to the method

The method is frozen at tag `v1.0-prereg` of the seven-task study (PREREG.md), and the frozen text gets editorial fixes only, each logged in `docs/CHANGELOG.md`. A change of method is a new version: it's proposed in an issue, logged in `CHANGELOG.md` with a task version bump, and applies to new runs only.

## Adding a platform

Other GTM platforms can be tested on the same 50 accounts and listed next to the original three. To add one:

1. **Ask for the accounts file.** It names one contact per account, so it isn't in the repo: open an issue titled "Data request" ([PRIVACY.md](PRIVACY.md) says how it's handled).
2. **Run the same agent task.** The prompt in `tasks/precall-briefs.md`, Claude Code on the same model, a 60-minute limit, and only that platform's own tools (CLI, API or MCP). The Harbor task in `harbor/write-precall-briefs/` is the easiest way to keep the setup identical; swap in the platform's credentials and tool note.
3. **Get it reviewed the same way.** We run the same blind AI reviewer and rubric (`scripts/ai_review.py`) on the same 20 accounts used for the other platforms, and score it with `scoring/scorers.py`.
4. **Send the run folder** (output, transcript, usage) privately for audit. The attempt is logged in [REPRODUCTIONS.md](REPRODUCTIONS.md).

A new platform is listed in RESULTS.md as a **later addition**, with its run date, separate from the three original runs, because platforms and models change over time. A vendor that ran it can choose to be named or listed anonymously.

## Code changes

Pull requests are welcome for bugs in the scoring code, the tests or the docs. Every pull request:

- runs the tests (`python -I -m unittest discover -s tests`) and the CI checks: no secrets, no personal data. Maintainers run `scripts/check_names.sh` before every push, which checks every commit for the real vendor names against a list kept outside the repository;
- needs a review from the code owners (`.github/CODEOWNERS`);
- changes no committed result unless it fixes a confirmed error, logged as above.

## Re-running the benchmark

See "Reproduce it" in the [README](../README.md), and tell us how it went with the **Reproduction report** issue template; we log every attempt in [REPRODUCTIONS.md](REPRODUCTIONS.md). If you publish your own run, please say which version of the method and of `benchkit` you used, and cite this repository (`CITATION.cff`).
