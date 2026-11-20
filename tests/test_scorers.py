"""End-to-end tests on throwaway fixture data (example.com domains). Run:
    python3 -I -m unittest discover -s tests
"""
import csv
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.environ["BENCH_REPO"] = str(REPO)
try:
    import benchkit  # noqa: F401
except ImportError:
    sys.path.insert(0, str(REPO.parent / "benchkit"))

from benchkit import agent, cli, costs, paths, review, runs  # noqa: E402

DOMAINS = [f"d{i}.example.com" for i in range(1, 5)]


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class HarnessTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        cfg = json.loads((REPO / "config" / "bench.json").read_text())
        cfg["tasks"]["T6"]["rows"] = 4
        cfg["tasks"]["T6"]["review"]["sample"] = 2
        (root / "cfg.json").write_text(json.dumps(cfg))
        os.environ["BENCH_ROOT"] = str(root)
        os.environ["BENCH_CONFIG"] = str(root / "cfg.json")
        self.root, self.cfg = root, paths.load_config()
        write_csv(paths.datasets() / "t6-accounts.csv", ["domain", "account_name", "contact_name", "contact_title"],
                  [[d, f"Account {i}", f"Contact {i}", "VP Sales"] for i, d in enumerate(DOMAINS, 1)])

    def tearDown(self):
        self.tmp.cleanup()
        os.environ.pop("BENCH_ROOT", None)
        os.environ.pop("BENCH_CONFIG", None)

    def _run(self, platform, blank=()):
        r = runs.new_run(self.cfg, "T6", platform, "agent", "agent-x", "agent", "self-serve monthly")
        write_csv(runs.run_dir(r["run_id"]) / "output" / "output.csv", self.cfg["tasks"]["T6"]["output_columns"],
                  [[d, "does x", "news https://example.com/n", "priority", "" if d in blank else "Hi"] for d in DOMAINS])
        return r["run_id"]

    def _score(self, run_id, ratings):
        write_csv(runs.run_dir(run_id) / "review" / "t6-scores.csv",
                  ["domain", "reviewer", "accuracy", "specificity", "usefulness", "fabricated"], ratings)
        cli.main(["score", run_id])
        return runs.load(run_id)["score"]

    def test_t6_scoring(self):
        run_id = self._run("clay")
        # Two raters on d1: every rating is averaged; one "yes" from either rater marks the brief as fabricated.
        s = self._score(run_id, [[DOMAINS[0], "ai", 5, 4, 4, "no"], [DOMAINS[0], "human", 4, 4, 3, "yes"],
                                 [DOMAINS[1], "ai", 5, 5, 3, "no"]])
        m = s["metrics"]
        self.assertEqual((m["rows_filled"], m["reviewed_items"], m["fabrications"]), (4, 2, 1))
        self.assertEqual((m["mean_accuracy"], m["mean_specificity"], m["mean_usefulness"]), (4.67, 4.33, 3.33))
        self.assertEqual((s["proposed_status"], s["accepted_records"], s["accepted_rate"]), ("Pass", 4, 1.0))
        # A second fabricated brief, or accuracy under 3.5, misses the pass line.
        s = self._score(run_id, [[DOMAINS[0], "ai", 5, 4, 4, "yes"], [DOMAINS[1], "ai", 5, 5, 3, "yes"]])
        self.assertEqual((s["metrics"]["fabrications"], s["proposed_status"], s["accepted_records"]), (2, "Partial", 0))
        s = self._score(run_id, [[DOMAINS[0], "ai", 3, 4, 4, "no"], [DOMAINS[0], "human", 1, 4, 4, "no"]])
        self.assertEqual((s["metrics"]["reviewer_disagreements_over_1pt"], s["proposed_status"]), (1, "Partial"))
        # Clay's cost is data credits times the list price; action credits are a separate unit.
        runs.set_usage(run_id, units={"data_credits": 5.1})
        self.assertAlmostEqual(costs.run_costs(self.cfg, runs.load(run_id))["usage_cost_usd"], 0.255)
        self.assertAlmostEqual(costs.unit_cost(self.cfg, "clay", {"data_credits": 5.1, "actions": 50}), 0.455)

    def test_blank_cell_is_not_a_written_brief(self):
        run_id = self._run("provider_a", blank=DOMAINS[:1])
        s = self._score(run_id, [[DOMAINS[1], "ai", 5, 5, 5, "no"]])
        self.assertEqual((s["metrics"]["rows_filled"], s["accepted_rate"], s["proposed_status"]), (3, 0.75, "Partial"))

    def test_blind_review_uses_the_same_accounts_on_every_platform(self):
        ids = [self._run(p) for p in ("clay", "provider_a", "provider_b")]
        sheet, n = review.blind_sample(self.cfg, "T6")
        rows = read_rows(sheet)
        key = json.loads((sheet.parent / "T6-blind-key.json").read_text())
        picked = {run_id: {r["domain"] for r in rows if key[r["item_id"]] == run_id} for run_id in ids}
        self.assertEqual(n, 6)
        self.assertEqual(len(picked[ids[0]]), 2)
        self.assertTrue(picked[ids[0]] == picked[ids[1]] == picked[ids[2]])
        self.assertFalse(set(ids) & {v for r in rows for v in r.values()})   # the sheet hides which run a row came from
        # The audit helper: merge adds the latest round's human ratings to the AI's, and import puts them in each run.
        spec = importlib.util.spec_from_file_location("review_audit", REPO / "scripts" / "review_audit.py")
        audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audit)
        audit.REVIEW = sheet.parent
        for r in rows:
            r.update(reviewer="ai", accuracy="5", specificity="4", usefulness="4", fabricated="no")
        audit.write("T6-blind-ai.csv", list(rows[0]), rows)
        audit.make("T6")
        human = read_rows(sheet.parent / "T6-audit-r1.csv")
        self.assertEqual(len(human), 3)                          # one account (20% of 2 rounds up to 1), every platform
        self.assertEqual(len({h["domain"] for h in human}), 1)
        for h in human:
            h.update(accuracy="4", specificity="4", usefulness="2", fabricated="no")
        audit.write("T6-audit-r1.csv", list(human[0]), human)
        audit.merge("T6")
        self.assertFalse(audit.agree(rows[0], {**rows[0], "usefulness": "2"}))
        review.blind_import(self.cfg, "T6", sheet.parent / "T6-final.csv")
        cli.main(["score", ids[0]])
        m = runs.load(ids[0])["score"]["metrics"]
        self.assertEqual((m["reviewed_items"], m["mean_accuracy"], m["mean_usefulness"]), (2, 4.67, 3.33))

    def test_checksum_mismatch_is_refused(self):
        self._run("clay")
        with open(paths.datasets() / "t6-accounts.csv", "a") as f:
            f.write("d5.example.com,Account 5,Contact 5,CRO\n")
        with self.assertRaises(runs.RunError):
            self._run("provider_b")

    def test_agent_prompt_env_and_stream(self):
        os.environ["CLAY_API_KEY"] = "clay-secret-123"
        os.environ["PROVIDER_B_API_KEY"] = "provider-b-secret-456"
        try:
            r = runs.new_run(self.cfg, "T6", "clay", "agent", "agent-x", "agent", "self-serve monthly")
            prompt = agent.build_prompt(self.cfg, r)
            self.assertIn(r["run_id"], prompt)
            self.assertIn("CLAY_API_KEY", prompt)
            self.assertNotIn("clay-secret-123", prompt)
            # The Harbor instruction is this prompt (run named after the task) plus one environment note.
            harbor = (REPO / "harbor" / "write-precall-briefs" / "instruction.md").read_text()
            for line in agent.build_prompt(self.cfg, {**r, "run_id": "write-precall-briefs"}).splitlines():
                self.assertIn(line, harbor)
            env = agent._child_env(self.cfg, "clay")
            self.assertIn("CLAY_API_KEY", env)
            self.assertNotIn("PROVIDER_B_API_KEY", env)
            dry = agent.run_agent(self.cfg, r["run_id"], dry_run=True)
            self.assertIn("--strict-mcp-config", dry["cmd"])
            lines = [json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use"}, {"type": "text"}]}}),
                     json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use"}]}}),
                     json.dumps({"type": "result", "total_cost_usd": 1.25, "num_turns": 4})]
            steps, res = agent.parse_stream(lines)
            self.assertEqual(steps, 2)
            self.assertEqual(res["total_cost_usd"], 1.25)
            self.assertEqual(agent.redact("key=clay-secret-123", ["clay-secret-123"]), "key=***REDACTED***")  # gitleaks:allow (fake key)
        finally:
            os.environ.pop("CLAY_API_KEY", None)
            os.environ.pop("PROVIDER_B_API_KEY", None)

    def test_harbor_rubric_matches_the_review_script(self):
        tests = REPO / "harbor" / "write-precall-briefs" / "tests"
        spec = importlib.util.spec_from_file_location("ai_review", REPO / "scripts" / "ai_review.py")
        ai_review = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ai_review)
        self.assertEqual(json.loads((tests / "task.json").read_text())["rubric"], ai_review.RUBRICS["T6"][0])


if __name__ == "__main__":
    unittest.main()
