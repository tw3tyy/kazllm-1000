import json
import unittest
from pathlib import Path

import numpy as np

from paper.analysis import lib
from paper.analysis.run import macro_name

ROOT = Path(__file__).resolve().parents[1]


class HelperTests(unittest.TestCase):
    def test_macro_names_are_letters_only(self):
        self.assertEqual(macro_name("gemChrfKK"), "GemChrfKK")
        self.assertEqual(macro_name("labReference mismatch"), "LabReferenceMismatch")
        self.assertTrue(macro_name("ablFoneGapK5").isalpha())

    def test_latin_share(self):
        self.assertEqual(lib.latin_share("Қазақстан"), 0.0)
        self.assertEqual(lib.latin_share("Qazaqstan"), 1.0)
        self.assertAlmostEqual(lib.latin_share("ab вг"), 0.5)

    def test_prefix_matching_credits_shared_stems_only(self):
        full, hl, rl = lib.unigram_matches("кітаптарды оқыды", "кітаптар оқыды")
        self.assertEqual((full, hl, rl), (1, 2, 2))
        stem, _, _ = lib.unigram_matches("кітаптарды оқыды", "кітаптар оқыды", k=5)
        self.assertEqual(stem, 2)

    def test_holm_is_monotone(self):
        self.assertEqual(lib.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


class ReproductionTests(unittest.TestCase):
    """The new analysis must reproduce the numbers already reported in Assignment 4."""

    @classmethod
    def setUpClass(cls):
        bench, cls.ps, _ = lib.load_benchmark(ROOT)
        out = lib.load_outputs(ROOT / "outputs/gemini-3.5-flash-lite.jsonl", cls.ps)
        cls.rows = lib.mt_pairs(bench, cls.ps, out)
        cls.a4 = json.loads((ROOT / "assignment4/results/results.json").read_text())

    def test_gap_matches_assignment4(self):
        idx = lib.boot_indices(len(self.rows))
        gap = lib.gap_with_ci(lib.segment_stats(self.rows, "en2kk", "chrf2"),
                              lib.segment_stats(self.rows, "kk2en", "chrf2"), idx, "chrf2")
        ref = self.a4["gap_all"]
        np.testing.assert_allclose([gap["point"], gap["lo"], gap["hi"]], [ref["delta"], ref["lo"], ref["hi"]], atol=1e-9)

    def test_qa_baselines_match_demo_rule(self):
        fixed, rand = lib.qa_baseline_answers(self.ps)
        a, r = lib.score_qa(self.ps, fixed), lib.score_qa(self.ps, rand)
        self.assertEqual((a["acc_kk"], a["acc_en"]), (0.195, 0.195))
        self.assertEqual((r["acc_kk"], r["acc_en"], r["kk_only"], r["en_only"]), (0.185, 0.27, 29, 46))


if __name__ == "__main__":
    unittest.main()
