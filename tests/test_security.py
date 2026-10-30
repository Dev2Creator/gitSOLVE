import unittest
from gitsolve.security import (
    sanitize_terminal_output,
    sanitize_repo_metadata,
    validate_repo_full_name,
)

class TestSecurity(unittest.TestCase):
    def test_strip_ansi_escapes(self):
        raw = "\033[31mDangerous Red\033[0m"
        clean = sanitize_terminal_output(raw)
        self.assertEqual(clean, "Dangerous Red")
        self.assertNotIn("\033", clean)

    def test_strip_terminal_control_characters(self):
        # Bell, backspace, null bytes
        raw = "Hello\x07\x08World\x00!"
        clean = sanitize_terminal_output(raw)
        self.assertEqual(clean, "HelloWorld!")

    def test_nfkc_unicode_normalization(self):
        # Compatibility characters (e.g. ligature or fullwidth)
        raw = "ｆｕｌｌｗｉｄｔｈ"
        clean = sanitize_terminal_output(raw)
        self.assertEqual(clean, "fullwidth")

    def test_max_length_truncation(self):
        raw = "A" * 500
        clean = sanitize_terminal_output(raw, max_length=100)
        self.assertEqual(len(clean), 100)
        self.assertTrue(clean.endswith("..."))

    def test_single_line_enforcement(self):
        raw = "Line 1\nLine 2\r\nLine 3"
        clean = sanitize_terminal_output(raw, allow_newlines=False)
        self.assertEqual(clean, "Line 1 Line 2 Line 3")

    def test_sanitize_repo_metadata(self):
        repo_data = {
            "name": "malicious\033[2Jrepo",
            "description": "Hack the \x07planet!\r\nSecond line",
            "stars": 5,
        }
        cleaned = sanitize_repo_metadata(repo_data)
        self.assertEqual(cleaned["name"], "maliciousrepo")
        self.assertNotIn("\033", cleaned["description"])
        self.assertNotIn("\x07", cleaned["description"])
        self.assertEqual(cleaned["stars"], 5)

    def test_validate_repo_full_name(self):
        self.assertTrue(validate_repo_full_name("torvalds/linux"))
        self.assertTrue(validate_repo_full_name("google/gemini-cli"))
        self.assertTrue(validate_repo_full_name("user_123/my.repo-name"))
        self.assertFalse(validate_repo_full_name("invalid;name"))
        self.assertFalse(validate_repo_full_name("../dangerous/path"))
        self.assertFalse(validate_repo_full_name("noslash"))

if __name__ == "__main__":
    unittest.main()
