"""AI reviewer for the Harbor grader: the same model, rules and rubric as the benchmark's own review
(scripts/ai_review.py), called through the Anthropic API with web search instead of the CLI.
HEAD is the seven-task study's shared reviewer header, kept byte for byte (its headcount rule serves other tasks).

Needs ANTHROPIC_API_KEY, or (outside the container) the signed-in `claude` CLI; with neither, review() returns None
and the grader reports the review as skipped.
JUDGE_CACHE (optional): a JSON file of earlier verdicts keyed by item_id, read first and updated per batch."""
import json
import os
import shutil
import subprocess

MODEL = "claude-sonnet-5-5"   # same reviewer model as the benchmark runs; the agents ran on Opus 5.5
HEAD = """You are reviewing benchmark output rows, blind. Today is {today}.
Check each item against public sources with web search; use the row's own values only as leads.
Rules (same as the human reviewer's):
- A criterion you cannot confirm from public sources counts as NOT met.
- Headcount: use the most recent reputable source (LinkedIn, company site, filings, recent press); if sources
  conflict, go with the most recent one.
- Search properly before deciding a fact is unsupported: the company newsroom/press releases, PR Newswire and
  BusinessWire, SEC EDGAR filings, investor-relations pages, and any URL in the row.
"""


def _call(client, prompt):
    """One review request; a server-tool turn that pauses is resumed until the model finishes."""
    messages = [{"role": "user", "content": prompt}]
    for _ in range(6):
        resp = client.beta.messages.create(
            model=MODEL, max_tokens=16000, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 40}],
            messages=messages)
        if resp.stop_reason == "refusal":
            raise SystemExit(f"reviewer declined: {getattr(resp.stop_details, 'category', None)}")
        if resp.stop_reason != "pause_turn":
            return "".join(b.text for b in resp.content if b.type == "text")
        messages.append({"role": "assistant", "content": resp.content})
    raise SystemExit("reviewer kept pausing; rerun the grader")


def _call_cli(prompt):
    """Outside the container, with no API key: the signed-in Claude CLI, as scripts/ai_review.py runs it."""
    out = subprocess.run(["claude", "-p", prompt, "--model", MODEL, "--output-format", "json",
                          "--allowedTools", "WebSearch", "WebFetch"], capture_output=True, text=True, timeout=1800, check=True)
    return json.loads(out.stdout)["result"]


def review(rubric, columns, items, today, batch=10):
    """items: [{"item_id": ..., <row fields>}]. columns: {name: allowed values (tuple) or "15" for 1-5}.
    Returns {item_id: {column: value, "note", "source"}} or None without an API key."""
    path = os.environ.get("JUDGE_CACHE", "")
    done = json.load(open(path, encoding="utf-8")) if path and os.path.exists(path) else {}
    todo = [i for i in items if i["item_id"] not in done]
    use_cli = bool(todo) and not os.environ.get("ANTHROPIC_API_KEY") and shutil.which("claude")
    if todo and not os.environ.get("ANTHROPIC_API_KEY") and not use_cli:
        return None
    if todo and not use_cli:
        import anthropic
        client = anthropic.Anthropic()
    shape = ", ".join(f'"{k}": ...' for k in columns)
    for start in range(0, len(todo), batch):
        part = todo[start:start + batch]
        prompt = (HEAD.format(today=today) + rubric + f'\nReply with ONLY a JSON array: [{{"item_id": "...", {shape}, '
                  '"note": "one short reason", "source": "main URL you relied on"}]\nItems:\n' + json.dumps(part, indent=1))
        text = _call_cli(prompt) if use_cli else _call(client, prompt)
        got = json.loads(text[text.index("["):text.rindex("]") + 1])
        ids = {i["item_id"] for i in part}
        for g in got:
            if g.get("item_id") not in ids:
                continue
            for k, allowed in columns.items():
                v = str(g.get(k))
                ok = v in allowed if isinstance(allowed, tuple) else (len(v) == 1 and allowed[0] <= v <= allowed[1])
                if not ok:
                    raise SystemExit(f"reviewer returned {k}={v!r} for {g['item_id']}")
            done[g["item_id"]] = {k: str(g[k]) for k in columns} | {"note": g.get("note", ""), "source": g.get("source", "")}
        missing = ids - set(done)
        if missing:
            raise SystemExit(f"reviewer skipped items {sorted(missing)}; rerun the grader")
        if path:
            json.dump(done, open(path, "w", encoding="utf-8"), indent=1)
    return {i["item_id"]: done[i["item_id"]] for i in items}
