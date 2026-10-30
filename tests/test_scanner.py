import unittest
from unittest.mock import MagicMock
from gitsolve.scanner import RepoInspector

class TestScanner(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_vault = MagicMock()
        self.mock_vault.is_seen.return_value = False
        self.inspector = RepoInspector(client=self.mock_client, vault=self.mock_vault)

    def test_search_radar_query_structure(self):
        self.mock_client.search_repositories.return_value = {
            "items": [
                {
                    "full_name": "solo/gem",
                    "stargazers_count": 3,
                    "forks_count": 0,
                    "pushed_at": "2024-05-01T00:00:00Z",
                    "created_at": "2023-11-01T00:00:00Z",
                    "description": "Quiet CLI gem",
                    "language": "Go",
                    "license": {"name": "MIT License"},
                }
            ]
        }
        self.mock_client.get_tree.return_value = {"tree": []}
        self.mock_client.get_languages.return_value = {"Go": 5000}
        self.mock_client.get_workflow_runs.return_value = {"workflow_runs": []}

        results = self.inspector.search_radar(
            topic="cli",
            language="go",
            min_stars=2,
            max_stars=5,
            limit=5,
        )

        self.mock_client.search_repositories.assert_called()
        call_query = self.mock_client.search_repositories.call_args[0][0]
        self.assertIn("stars:2..5", call_query)
        self.assertIn("topic:cli", call_query)
        self.assertIn("language:go", call_query)
        self.assertIn("fork:false", call_query)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["full_name"], "solo/gem")
        self.assertIn("overall_score", results[0])

    def test_forks_search(self):
        self.mock_client.get_repo.return_value = {
            "full_name": "original/repo",
            "stargazers_count": 100,
            "default_branch": "main",
        }
        self.mock_client.get_forks.return_value = [
            {
                "full_name": "active/fork",
                "stargazers_count": 5,
                "pushed_at": "2024-06-01T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "description": "Fork with custom modern fixes",
            }
        ]
        self.mock_client.compare_commits.return_value = {
            "status": "ahead",
            "ahead_by": 4,
            "behind_by": 2,
        }

        forks = self.inspector.search_forks("original/repo", limit=5)
        self.assertEqual(len(forks), 1)
        self.assertEqual(forks[0]["full_name"], "active/fork")
        self.assertEqual(forks[0]["ahead_by"], 4)

    def test_compare_repos(self):
        self.mock_client.get_repo.side_effect = [
            {
                "full_name": "repo/one",
                "stargazers_count": 3,
                "created_at": "2024-01-01T00:00:00Z",
                "pushed_at": "2024-06-01T00:00:00Z",
            },
            {
                "full_name": "repo/two",
                "stargazers_count": 5,
                "created_at": "2024-01-01T00:00:00Z",
                "pushed_at": "2024-06-01T00:00:00Z",
            },
        ]
        self.mock_client.get_tree.return_value = {"tree": []}
        self.mock_client.get_languages.return_value = {}
        self.mock_client.get_workflow_runs.return_value = {"workflow_runs": []}
        self.mock_client.get_commits.return_value = []

        comp = self.inspector.compare_repos("repo/one", "repo/two")
        self.assertEqual(comp["repo1"]["full_name"], "repo/one")
        self.assertEqual(comp["repo2"]["full_name"], "repo/two")
        self.assertIn("winner", comp)

    def test_get_readme(self):
        self.mock_client.get_readme.return_value = "# Sample Readme\nDetails here."
        res = self.inspector.get_readme("owner/repo")
        self.assertEqual(res, "# Sample Readme\nDetails here.")
        self.mock_client.get_readme.assert_called_with("owner/repo")

    def test_get_tree_structure(self):
        self.mock_client.get_tree.return_value = [
            {"path": "src/main.rs", "type": "blob", "size": 1024},
            {"path": "Cargo.toml", "type": "blob", "size": 256},
        ]
        res = self.inspector.get_tree_structure("owner/repo")
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["path"], "src/main.rs")
        self.assertEqual(res[0]["size"], 1024)

    def test_get_recent_commits(self):
        self.mock_client.get_commits.return_value = [
            {
                "sha": "abcdef1234567890",
                "commit": {
                    "message": "feat: implement radar scope\n\nMore details here",
                    "author": {"name": "Linus", "date": "2024-05-01T12:00:00Z"},
                },
                "author": {"login": "linus"},
            }
        ]
        res = self.inspector.get_recent_commits("owner/repo", limit=5)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["sha"], "abcdef1")
        self.assertEqual(res[0]["message"], "feat: implement radar scope")
        self.assertEqual(res[0]["author"], "Linus")

    def test_search_velocity(self):
        self.mock_client.search_repositories.return_value = {
            "items": [
                {
                    "full_name": "solo/velocity-gem",
                    "stargazers_count": 4,
                    "forks_count": 0,
                    "pushed_at": "2024-05-01T00:00:00Z",
                    "created_at": "2024-01-01T00:00:00Z",
                    "description": "High momentum",
                    "language": "Rust",
                }
            ]
        }
        self.mock_client.get_tree.return_value = {"tree": []}
        self.mock_client.get_languages.return_value = {"Rust": 5000}
        self.mock_client.get_workflow_runs.return_value = {"workflow_runs": []}

        res = self.inspector.search_velocity(language="rust", limit=5)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["full_name"], "solo/velocity-gem")

    def test_normalize_repo_name(self):
        from gitsolve.github import normalize_repo_name
        self.assertEqual(normalize_repo_name("https://github.com/astral-sh/uv"), "astral-sh/uv")
        self.assertEqual(normalize_repo_name("https://github.com/astral-sh/uv.git"), "astral-sh/uv")
        self.assertEqual(normalize_repo_name("git@github.com:owner/repo.git"), "owner/repo")
        self.assertEqual(normalize_repo_name("owner/repo/"), "owner/repo")
        self.assertEqual(normalize_repo_name("  owner/repo  "), "owner/repo")

if __name__ == "__main__":
    unittest.main()
