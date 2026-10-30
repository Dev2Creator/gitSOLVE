import unittest
from unittest.mock import patch, MagicMock
from gitsolve.ai import PollinationsClient

class TestAI(unittest.TestCase):
    def setUp(self):
        self.ai = PollinationsClient(timeout=1.0)

    def test_offline_fallback_verdict(self):
        repo = {
            "full_name": "solitary/b-tree",
            "description": "Lock-free B-tree storage engine",
            "primary_language": "Rust",
            "stars": 4,
            "has_tests": True,
            "has_ci": True,
            "age_text": "7 months old",
            "pushed_days": 2,
        }
        verdict = self.ai.generate_deep_verdict(repo)
        self.assertIn("verdict", verdict)
        self.assertIn("why_good", verdict)
        self.assertIn("underground_edge", verdict)
        self.assertIn("caveats", verdict)
        self.assertIn("Lock-free B-tree", verdict["verdict"])
        self.assertTrue("automated test suite" in verdict["why_good"].lower() or "rust" in verdict["why_good"].lower())

    @patch("gitsolve.ai.PollinationsClient.generate")
    def test_online_verdict_parsing(self, mock_generate):
        mock_generate.return_value = """
        {
            "verdict": "A minimal, highly optimized compiler runtime in Zig.",
            "why_good": "Zero allocator overhead and clean register allocation.",
            "underground_edge": "100x smaller binary than standard LLVM toolchains.",
            "caveats": "Experimental syntax, small community."
        }
        """
        repo = {"full_name": "zig/fast-rt", "stars": 5}
        verdict = self.ai.generate_deep_verdict(repo)
        self.assertEqual(verdict["verdict"], "A minimal, highly optimized compiler runtime in Zig.")
        self.assertIn("Zero allocator overhead", verdict["why_good"])
        self.assertIn("smaller binary", verdict["underground_edge"])

    def test_explain_repo_formatting(self):
        repo = {
            "full_name": "mod/cache",
            "description": "High performance LRU cache",
            "primary_language": "Go",
            "stars": 3,
        }
        text = self.ai.explain_repo(repo)
        self.assertIn("DETAILED VERDICT", text)
        self.assertIn("WHY THIS IS GOOD", text)
        self.assertIn("UNDERGROUND EDGE", text)
        self.assertIn("CAVEATS", text)

    def test_parse_natural_radar_query_heuristic(self):
        res = self.ai.parse_natural_radar_query("find me lightweight rust database tools under 10 stars")
        self.assertEqual(res["language"], "rust")
        self.assertEqual(res["min_stars"], 2)

    def test_explain_repo_with_readme_snippet(self):
        repo = {
            "full_name": "simd/matrix",
            "description": "Fast matrix operations",
            "primary_language": "C",
            "stars": 4,
            "has_tests": True,
            "has_ci": True,
        }
        readme_snippet = "# SIMD Matrix\nHigh throughput matrix vector multiplications using AVX-512 intrinsics."
        text = self.ai.explain_repo(repo, readme_snippet=readme_snippet)
        self.assertIn("DETAILED VERDICT", text)
        self.assertIn("WHY THIS IS GOOD", text)
        self.assertIn("UNDERGROUND EDGE", text)
        self.assertIn("CAVEATS", text)

if __name__ == "__main__":
    unittest.main()
