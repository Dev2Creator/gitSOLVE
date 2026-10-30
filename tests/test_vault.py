import unittest
import tempfile
import json
from pathlib import Path
from gitsolve.vault import Vault

class TestVault(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_vault.db"
        self.vault = Vault(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_list_gem(self):
        gem = {
            "full_name": "test/sleeper",
            "stars": 4,
            "overall_score": 92,
            "health_score": 88,
            "discovery_score": 95,
            "primary_language": "Rust",
            "description": "A very quiet gem",
            "html_url": "https://github.com/test/sleeper",
            "age_text": "6 months old",
        }
        success = self.vault.save_gem(gem, tags=["rust", "database"], notes="Remarkable B-Tree structure")
        self.assertTrue(success)

        gems = self.vault.list_gems()
        self.assertEqual(len(gems), 1)
        saved = gems[0]
        self.assertEqual(saved["full_name"], "test/sleeper")
        self.assertEqual(saved["discovered_stars"], 4)
        self.assertEqual(saved["last_checked_stars"], 4)
        self.assertIn("rust", saved["tags"])
        self.assertIn("database", saved["tags"])
        self.assertEqual(saved["notes"], "Remarkable B-Tree structure")

    def test_tag_filtering(self):
        gem1 = {"full_name": "a/b", "stars": 3, "overall_score": 85}
        gem2 = {"full_name": "c/d", "stars": 5, "overall_score": 90}
        self.vault.save_gem(gem1, tags=["ai", "compiler"])
        self.vault.save_gem(gem2, tags=["web", "compiler"])

        ai_gems = self.vault.list_gems(tag="ai")
        self.assertEqual(len(ai_gems), 1)
        self.assertEqual(ai_gems[0]["full_name"], "a/b")

        compiler_gems = self.vault.list_gems(tag="compiler")
        self.assertEqual(len(compiler_gems), 2)

    def test_seen_tracking(self):
        self.assertFalse(self.vault.is_seen("dev/project"))
        self.vault.mark_seen("dev/project", source="radar")
        self.assertTrue(self.vault.is_seen("dev/project"))

        candidates = ["dev/project", "fresh/project"]
        unseen = self.vault.filter_unseen(candidates)
        self.assertEqual(unseen, ["fresh/project"])

    def test_export_and_import_json(self):
        gem = {"full_name": "gem/one", "stars": 2, "overall_score": 89}
        self.vault.save_gem(gem, tags=["tool"], notes="Awesome")

        json_file = Path(self.temp_dir.name) / "export.json"
        self.vault.export_json(json_file)
        self.assertTrue(json_file.exists())

        # Test importing into a fresh vault
        fresh_db = Path(self.temp_dir.name) / "fresh_vault.db"
        fresh_vault = Vault(db_path=fresh_db)
        imported_count = fresh_vault.import_json(json_file)
        self.assertEqual(imported_count, 1)
        self.assertEqual(len(fresh_vault.list_gems()), 1)

    def test_curator_rank(self):
        # 0 gems
        rank, _ = self.vault.get_curator_rank()
        self.assertEqual(rank, "NOVICE OBSERVER")

        for i in range(5):
            self.vault.save_gem({"full_name": f"user/gem_{i}", "stars": i + 2, "overall_score": 80})

        rank, _ = self.vault.get_curator_rank()
        self.assertTrue("CODE ARCHAEOLOGIST" in rank)

    def test_export_markdown(self):
        gem = {
            "full_name": "gem/alpha",
            "stars": 3,
            "overall_score": 90,
            "primary_language": "Rust",
            "html_url": "https://github.com/gem/alpha",
        }
        self.vault.save_gem(gem, notes="Handcrafted binary", tags=["cli", "rust"])
        md_file = Path(self.temp_dir.name) / "portfolio.md"
        content = self.vault.export_markdown(md_file)
        self.assertTrue(md_file.exists())
        self.assertIn("gitSOLVE Curator Portfolio", content)
        self.assertIn("gem/alpha", content)
        self.assertIn("Handcrafted binary", content)

if __name__ == "__main__":
    unittest.main()
