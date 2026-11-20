# Benchmark card: AI pre-call brief benchmark

Version 1.0, 19 November 2026. The detail behind each line is in the [README](../README.md), [METHODOLOGY.md](../METHODOLOGY.md) and [RESULTS.md](../RESULTS.md).

**Results as of 9–10 November 2026 (UTC).** These numbers show the three platforms as they were on the days of the runs. Platforms change their products, data and prices. Run the benchmark again before relying on these results after mid-2027, or sooner if a platform changes its product.

**Purpose.** To measure how well one AI agent writes pre-call research briefs for a sales team when it may use only one data platform's own tools: Clay, and two anonymized data providers.

**What it measures.** For 50 accounts on each platform: how many briefs the agent wrote; how accurate, specific and useful a blind review found a sample of 20; how many of those stated a fabricated fact; and the run's steps, minutes, platform credit cost and model cost.

**What it doesn't measure.** The platforms' data quality in general, any other task, people using the web apps, plan and seat fees, or how much results vary from run to run.

**Intended uses.** Seeing how the task, the scoring and the review were set up. Rerunning the Clay task. Checking the published numbers. Citing the results together with their limits.

**Out-of-scope uses.** Ranking the three platforms overall. Treating a gap as real when the intervals in RESULTS.md overlap. Making a buying decision on this alone. Working out who the two anonymized providers are.

**Data.** 50 accounts at public companies, each with one contact's name and title. The accounts file, the briefs, the per-brief ratings and the run folders are private, because they name real people. Researchers can ask for them for 90 days after publication (README, "Data on request"); after that they are deleted. This repository holds totals only. [PRIVACY.md](PRIVACY.md) says what personal data was used and how a person named in it can ask about theirs.

**Limitations.**

- One run per platform, so run-to-run variation is not measured.
- The scores come from an AI reviewer. A person audited it twice and agreed with it on 58% and then 78% of the audited briefs, under the 85% bar set beforehand.
- 20 of each platform's 50 briefs were reviewed.
- The three platforms produced their briefs in different ways, each chosen by the agent: Clay's own AI wrote them; on Provider A the agent wrote them from the platform's data; on Provider B a script filled sentence templates.
- One task of seven is published alone. The study's pre-registered plan was to publish all seven together, so this departs from that plan.
- The review method changed after the method was frozen, and the competitors were not offered a review before publication ([CHANGELOG.md](CHANGELOG.md)).
- Not independently reviewed.

**Disclosure.** Run by The Prompting Company. The study's tasks were chosen from questions buyers ask AI assistants, including ones on which Clay wanted to be cited more.

**Maintenance and contact.** Maintained by [The Prompting Company](https://promptingcompany.com). Report a wrong number with the "Results or scoring error" issue template and a reproduction attempt with "Reproduction report" ([REPRODUCTIONS.md](REPRODUCTIONS.md)). Security and data concerns go through [SECURITY.md](../SECURITY.md). Corrections are dated in CHANGELOG.md.
