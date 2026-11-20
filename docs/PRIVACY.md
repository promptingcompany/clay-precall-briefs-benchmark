# Privacy

What personal data this benchmark used, why, and what a person named in it can do. Last updated 19 November 2026. The benchmark is run by [The Prompting Company](https://promptingcompany.com).

**What was used.** The input is a file of 50 real accounts. For each account it holds the company's domain and name, and one business contact: a name and a job title. It holds no email address, phone number or other detail about the person. The outputs are briefs about the companies; a brief's opening line can address the contact by first name.

**Where it came from.** The companies come from a pool of public companies, so their news can be checked against filings and press releases ([METHODOLOGY.md](../METHODOLOGY.md) section 3). Inputs come only from public filings and registers ([SECURITY.md](../SECURITY.md), "Data concerns").

**Why it was used.** Only to run and score the benchmark. Nobody on the list was contacted: no email, sequence, call or message was sent to any contact ([METHODOLOGY.md](../METHODOLOGY.md) section 8).

**Legal basis.** Legitimate interests: business contact details that were already public, used for research into how data tools perform. The use is narrow: a name and a job title, used for scoring only.

**What is published.** Nothing personal. This repository holds totals and averages per platform only. The accounts file, the briefs, the per-brief ratings and the run folders are private and are not committed.

**Who has seen the private files.**

- The Prompting Company, which ran the benchmark.
- The tools used in the runs. The AI agent (Claude Code on an Anthropic model) read the accounts file and worked through the platform it was testing, so account details, which can include the contact's name and title, may have been sent to that platform's tools: Clay, or one of the two anonymized providers. The AI reviewer (an Anthropic model with web search) read the briefs.
- Researchers who ask. To ask, open an issue titled "Data request" on this repository. We share the private files with researchers only, and not in public ([README](../README.md#data-on-request), "Data on request").

**How long it is kept.** The private files are deleted 90 days after publication ([METHODOLOGY.md](../METHODOLOGY.md) section 8). After that only the published totals remain.

**If you are named in the file.** You can ask what we hold about you, or ask to be removed. There are three ways:

- By email: [support@promptingco.com](mailto:support@promptingco.com), subject "Privacy request".
- Privately, through GitHub: open this repository's **Security** tab and choose **Report a vulnerability**. This is the route [SECURITY.md](../SECURITY.md) gives for data concerns.
- Or open an issue titled "Privacy request". Issues are public, so don't put personal details in it; we will reply with a private way to continue.

Removing a person changes none of the published numbers, because they hold no personal data.

**GDPR and UK GDPR.** The accounts file does not record where a contact lives or works, so we don't know whether any of them are in the EU or the UK. If any are, the EU GDPR or the UK GDPR may apply to this use. The legal basis would be legitimate interests, as above, and the person would have the rights those laws give, including to see the data, have it erased, object to its use, and complain to their data protection authority. The two routes above work for any of these.
