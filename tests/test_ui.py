import unittest
from gitsolve.ui import (
    get_artistic_emblem,
    get_artistic_wordmark,
    get_layout_width,
    get_menu_indent,
    command_choice,
    get_theme,
    get_personalized_greeting,
    render_image_halfblocks,
    get_mascot_lines,
    get_asset_path,
    MASCOTS,
    THEMES,
)
from pathlib import Path

class TestUI(unittest.TestCase):
    def test_artistic_emblem_generation(self):
        theme = THEMES["lavender_night"]
        lines = get_artistic_emblem(theme)
        self.assertEqual(len(lines), 7)
        plain_text = "".join(line.plain for line in lines)
        self.assertIn("◈", plain_text)
        self.assertIn("✦", plain_text)

    def test_artistic_wordmark_generation(self):
        theme = THEMES["warm_earth"]
        lines = get_artistic_wordmark(theme)
        self.assertEqual(len(lines), 3)
        plain_text = "".join(line.plain for line in lines)
        self.assertIn("█▀▀", plain_text)
        self.assertIn("▀▀▀", plain_text)

    def test_layout_width_and_indent(self):
        w = get_layout_width()
        self.assertGreaterEqual(w, 56)
        self.assertLessEqual(w, 104)

        indent = get_menu_indent()
        self.assertGreaterEqual(indent, 0)

    def test_command_choice_formatting(self):
        choice = command_choice("radar", "Scan underground repos", "radar", "✦")
        self.assertEqual(choice.value, "radar")
        self.assertIn("/radar", choice.title)
        self.assertIn("│", choice.title)
        self.assertIn("Scan underground repos", choice.title)

    def test_personalized_greeting(self):
        greeting = get_personalized_greeting("cutie", "she/her")
        self.assertIn("cutie", greeting)
        self.assertIn("(she/her)", greeting)
        self.assertIn("Radar ready.", greeting)

        # Empty pronouns
        greeting_no_pronouns = get_personalized_greeting("Explorer", "")
        self.assertIn("Explorer", greeting_no_pronouns)
        self.assertNotIn("()", greeting_no_pronouns)

    def test_mascots_dict(self):
        self.assertIn("hoodie", MASCOTS)
        self.assertIn("zerotwo_lean", MASCOTS)
        self.assertIn("rikka", MASCOTS)
        self.assertIn("pikachu", MASCOTS)
        self.assertIn("crystal", MASCOTS)
        for key, info in MASCOTS.items():
            self.assertIn("name", info)
            self.assertIn("description", info)

    def test_render_image_halfblocks(self):
        # Non-existent path returns empty list
        missing = render_image_halfblocks(Path("does_not_exist.png"))
        self.assertEqual(missing, [])

        # Valid asset path
        hoodie_path = get_asset_path("clean_mascot_hoodie.png")
        self.assertIsNotNone(hoodie_path)
        lines = render_image_halfblocks(hoodie_path, target_width_box=28, max_lines=8)
        self.assertGreater(len(lines), 0)
        self.assertLessEqual(len(lines), 8)

    def test_get_mascot_lines_fallback(self):
        theme = THEMES["warm_earth"]
        crystal_lines = get_mascot_lines(theme, mascot_key="crystal")
        self.assertEqual(len(crystal_lines), 7)

if __name__ == "__main__":
    unittest.main()
