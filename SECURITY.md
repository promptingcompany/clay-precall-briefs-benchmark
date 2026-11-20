# Security policy

## Reporting a vulnerability

Please report security problems privately through GitHub: open this repository's **Security** tab and choose **Report a vulnerability**. Don't open a public issue for a security problem.

Include what you found, where (file and line, or the command you ran), and how to reproduce it. We aim to acknowledge reports within 5 business days.

## What counts

- Code that could leak a credential: an API key, token or `.env` value reaching a log, an audit file, a transcript or a committed file.
- Personal data reaching a committed file: a person's name, email address or phone number. This repo publishes aggregates only; the accounts file, which names a contact at each account, stays in the gitignored `private/` folder.
- Anything that lets a benchmark run reach a live system it shouldn't, such as a real outreach channel.
- A vulnerability in a dependency or in the GitHub Actions this repo uses.

## Data concerns

If you believe your own details were used to build a benchmark input, report it the same way. Inputs come only from public filings and registers, are never published, are shared only with researchers who ask (README, "Data on request"), and are deleted 90 days after the results are published. [PRIVACY.md](docs/PRIVACY.md) has the full statement.

## Supported versions

Only the latest commit on `main` and the most recent release tag are supported.

## Handling secrets in this repo

- Credentials live only in a local `.env` file, which is gitignored. `.env.example` lists the names, never values.
- The harness redacts credential values from the transcripts and work files it saves (METHODOLOGY.md section 6). Those run folders are private.
- CI runs gitleaks on every push; GitHub secret scanning and push protection are turned on when the repository is public.
