import unittest
from datetime import datetime, timezone, timedelta
from gitsolve.scoring import calculate_repository_score, EvidenceStatus

class TestScoring(unittest.TestCase):
    def test_ideal_sleeper_scoring(self):
        # 4 stars, active, test suite, passing CI, 9 months old, clean license
        now = datetime.now(timezone.utc)
        pushed = (now - timedelta(days=5)).isoformat()
        created = (now - timedelta(days=270)).isoformat()

        repo = {
            "full_name": "alpha/engine",
            "stargazers_count": 4,
            "forks_count": 1,
            "created_at": created,
            "pushed_at": pushed,
            "description": "High performance B-tree engine written in pure Rust.",
            "license": {"name": "MIT License"},
            "has_issues": True,
        }
        signals = {
            "has_tests": True,
            "test_file_count": 8,
            "has_ci": True,
            "ci_conclusion": "success",
            "has_readme": True,
            "readme_bytes": 3500,
            "has_manifest": True,
            "tree_item_count": 28,
            "recent_commit_count": 6,
        }

        eval_res = calculate_repository_score(repo, signals)

        self.assertGreaterEqual(eval_res.overall_score, 85)
        self.assertGreaterEqual(eval_res.health_score, 80)
        self.assertGreaterEqual(eval_res.discovery_score, 85)
        self.assertIn("MYTHIC SLEEPER", eval_res.rarity_tier)
        self.assertEqual(eval_res.confidence, "high")
        self.assertTrue(any("test" in ev.lower() for ev in eval_res.positive_evidence))
        self.assertTrue(any("ci" in ev.lower() for ev in eval_res.positive_evidence))

    def test_abandoned_popular_repo(self):
        # High stars, pushed 3 years ago, no tests, no CI
        now = datetime.now(timezone.utc)
        pushed = (now - timedelta(days=1200)).isoformat()
        created = (now - timedelta(days=1500)).isoformat()

        repo = {
            "full_name": "hype/framework",
            "stargazers_count": 5000,
            "forks_count": 400,
            "created_at": created,
            "pushed_at": pushed,
            "description": "Old framework",
            "license": None,
            "has_issues": False,
        }
        signals = {
            "has_tests": False,
            "test_file_count": 0,
            "has_ci": False,
            "ci_conclusion": None,
            "has_readme": False,
            "readme_bytes": 0,
            "has_manifest": False,
            "tree_item_count": 5,
            "recent_commit_count": 0,
        }

        eval_res = calculate_repository_score(repo, signals)
        self.assertLess(eval_res.discovery_score, 40)
        self.assertLess(eval_res.health_score, 40)
        self.assertTrue(any("stale" in r.lower() or "days ago" in r.lower() for r in eval_res.negative_risks))
        self.assertTrue(any("license" in r.lower() for r in eval_res.negative_risks))

    def test_evidence_status_integrity(self):
        repo = {
            "full_name": "mod/tool",
            "stargazers_count": 3,
            "forks_count": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "pushed_at": "2024-06-01T00:00:00Z",
        }
        # When signals are omitted, tests should be NOT_CHECKED
        eval_res_empty = calculate_repository_score(repo, {})
        self.assertEqual(eval_res_empty.evidence_status.get("tests"), EvidenceStatus.NOT_CHECKED)

        # When tests is False, tests should be UNKNOWN (not detected)
        eval_res_false = calculate_repository_score(repo, {"has_tests": False})
        self.assertEqual(eval_res_false.evidence_status.get("tests"), EvidenceStatus.UNKNOWN)

if __name__ == "__main__":
    unittest.main()
