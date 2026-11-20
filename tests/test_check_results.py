"""The committed RESULTS.md, README.md and results files agree, and the check catches a number that doesn't.
Also kappa, on worked examples. Run:
    python3 -I -m unittest discover -s tests
"""
import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHECKED = ("scripts/check_results.py", "results", "config/bench.json", "README.md", "RESULTS.md", "METHODOLOGY.md",
           "docs/DATA-DICTIONARY.md", "harbor/README.md")
sys.path.insert(0, str(REPO / "scripts"))
from review_stats import kappa  # noqa: E402


def check(repo):
    return subprocess.run([sys.executable, "-I", str(repo / "scripts" / "check_results.py")], capture_output=True, text=True)


class CheckResultsTest(unittest.TestCase):
    def test_published_numbers_match_results_files(self):
        r = check(REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_changed_number_in_a_sentence_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)
            for name in CHECKED:
                (copy / name).parent.mkdir(parents=True, exist_ok=True)
                (shutil.copytree if (REPO / name).is_dir() else shutil.copy)(REPO / name, copy / name)
            with open(copy / "results" / "t6-results.csv", newline="", encoding="utf-8") as f:
                steps = next(csv.DictReader(f))["steps"]  # Clay's row comes first
            text = (copy / "RESULTS.md").read_text(encoding="utf-8")
            self.assertIn(f"{steps} steps", text)
            (copy / "RESULTS.md").write_text(text.replace(f"{steps} steps", f"{int(steps) + 1} steps"), encoding="utf-8")
            r = check(copy)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn(f"{steps} steps", r.stdout)


class KappaTest(unittest.TestCase):
    def test_yes_no_ratings(self):
        def same(a, b):
            return a == b

        # The textbook case: 50 items, both yes on 20, both no on 15, split 5 and 10. Seen 0.7, chance 0.5.
        pairs = [("y", "y")] * 20 + [("y", "n")] * 5 + [("n", "y")] * 10 + [("n", "n")] * 15
        self.assertEqual(kappa(pairs, same), Fraction(2, 5))
        self.assertEqual(kappa([("n", "y"), ("n", "n")], same), 0)  # one rater never says yes: no better than chance
        self.assertIsNone(kappa([("n", "n")] * 3, same))  # both always say no: undefined

    def test_linear_weights_on_scores(self):
        def near(a, b):
            return 1 - Fraction(abs(a - b), 4)

        self.assertEqual(kappa([(1, 1), (5, 5), (3, 3)], near), 1)
        self.assertEqual(kappa([(1, 2), (2, 1)], near), -1)  # seen 3/4, chance 7/8
        # 1 point apart on one of three items: seen 11/12, chance 19/36
        self.assertEqual(kappa([(1, 1), (3, 4), (5, 5)], near), Fraction(14, 17))


if __name__ == "__main__":
    unittest.main()
