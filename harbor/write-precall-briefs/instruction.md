Benchmark task T6-v1 (run write-precall-briefs).

We sell a sales-data platform to B2B SaaS companies. For each account in input/t6-accounts.csv, produce a 3-bullet pre-call brief (what the company does; one recent development in the last 6 months with a source URL; one likely priority for the contact's role) and one personalized opening line. Save output/output.csv with exactly these columns: domain, bullet_1, bullet_2, bullet_3, first_line.

Rules:
- Use only Clay, through the Clay CLI or Clay API. Do not use any other data provider, scraper or website as a data source; you may read Clay's public documentation.
- Credentials are in the environment variable(s) CLAY_API_KEY. Never print, log or save them.
- Name any table, list, workbook or workflow you create exactly 'write-precall-briefs' so its usage can be attributed to this run.
- Never send email, sequences, calls or messages to any contact. Write to a CRM only if the task says so, and only to the sandbox named in the task.
- Do not fabricate, mock or hard-code data. If the platform returns nothing for a row, leave that cell blank.
- If a step has no documented way to do it on Clay, write output/not_supported.md naming the step and citing the documentation URL you checked, then do as much of the rest as you can.
- Write runnable code you used into the work/ folder and save the final result exactly as specified.

Environment note: Clay's CLI needs an interactive browser login, which isn't possible here, so use Clay's Public API with the key in CLAY_API_KEY. Saved Clay routines are in environment variables named CLAY_ROUTINE_ID_* (run one with POST /public/v0/routines/{routine_id}/run), and Clay's docs are at https://developers.clay.com. Save the output file as you go, so work isn't lost if the time limit is reached.

When finished, reply with a short summary of what you did and anything you could not do.
