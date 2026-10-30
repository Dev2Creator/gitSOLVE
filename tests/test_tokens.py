# gitSOLVE ✦ Tests for the "Iris" Design Token System
import unittest
from rich.text import Text

from gitsolve import tokens as tk
from gitsolve.tokens import (
    THEMES,
    hex_to_rgb,
    rgb_to_hex,
    lerp_color,
    gradient_text,
    gradient_badge,
    gradient_meter,
    gradient_rule,
    gradient_sparkline,
    role,
    tier_visual,
    tier_icon,
    fmt_size,
)
from gitsolve.ui import tree_to_lines
from gitsolve.scanner import cadence_summary


class TestColorPrimitives(unittest.TestCase):
    def test_hex_roundtrip(self):
        self.assertEqual(hex_to_rgb("#F29265"), (242, 146, 101))
        self.assertEqual(hex_to_rgb("#F92"), (255, 153, 34))
        self.assertEqual(rgb_to_hex((242, 146, 101)), "#F29265")

    def test_lerp_endpoints_and_middle(self):
        self.assertEqual(lerp_color("#000000", "#FFFFFF", 0.0), "#000000")
        self.assertEqual(lerp_color("#000000", "#FFFFFF", 1.0), "#FFFFFF")
        mid = lerp_color("#000000", "#FFFFFF", 0.5)
        self.assertEqual(mid, "#808080")
        # Clamped out-of-range t
        self.assertEqual(lerp_color("#000000", "#FFFFFF", 2.0), "#FFFFFF")


class TestGradientRenderables(unittest.TestCase):
    def test_gradient_text_plain_preserved(self):
        t = gradient_text("RADIO", "#FF0000", "#00FF00", bold=True)
        self.assertIsInstance(t, Text)
        self.assertEqual(t.plain, "RADIO")
        self.assertEqual(len(t.spans), 5)

    def test_gradient_badge(self):
        t = gradient_badge("GEM", "#111111", "#EEEEEE")
        self.assertEqual(t.plain, " GEM ")
        self.assertEqual(len(t.spans), 5)

    def test_gradient_meter_structure(self):
        markup = gradient_meter(74, 100, width=10, start="#FF0000", end="#00FF00", empty="#111111")
        self.assertIn("▰", markup)
        self.assertIn("▱", markup)
        self.assertIn("74", markup)
        # Filled should have 7 blocks, empty 3
        self.assertEqual(markup.count("▰"), 7)
        self.assertEqual(markup.count("▱"), 3)

    def test_gradient_meter_clamps(self):
        over = gradient_meter(150, 100, width=5, show_score=False)
        self.assertEqual(over.count("▰"), 5)
        self.assertEqual(over.count("▱"), 0)
        under = gradient_meter(-4, 100, width=5, show_score=False)
        self.assertEqual(under.count("▰"), 0)

    def test_gradient_rule_and_sparkline(self):
        rule = gradient_rule(40, "#111111", "#EEEEEE")
        self.assertEqual(rule.count("─"), 40)
        spark = gradient_sparkline([1, 5, 2, 9, 4])
        self.assertEqual(len(spark.splitlines()), 1)
        self.assertNotEqual(spark, "")


class TestThemesAndRoles(unittest.TestCase):
    def test_all_themes_have_iris_roles(self):
        for name, theme in THEMES.items():
            for key in ("accent", "cream", "muted", "border", "selected", "gold", "mythic",
                        "surface", "success", "warn", "danger", "info", "grad_a", "grad_b"):
                self.assertIn(key, theme, f"{name} missing {key}")

    def test_role_fallback(self):
        fake = {"accent": "#123456"}
        self.assertEqual(role(fake, "success"), tk.DEFAULT_ROLES["success"])
        self.assertEqual(role(fake, "accent"), "#123456")
        self.assertEqual(role({}, "unknown_role"), "#F29265")


class TestTierVisuals(unittest.TestCase):
    def test_tier_thresholds(self):
        theme = THEMES["warm_earth"]
        label, start, end = tier_visual(94, theme)
        self.assertIn("MYTHIC", label)
        label, start, end = tier_visual(80, theme)
        self.assertIn("GOLD", label)
        label, start, end = tier_visual(60, theme)
        self.assertIn("HIDDEN", label)

    def test_tier_icon(self):
        self.assertEqual(tier_icon(95), "💎")
        self.assertEqual(tier_icon(75), "🔥")
        self.assertEqual(tier_icon(50), "✨")


class TestFmtSize(unittest.TestCase):
    def test_sizes(self):
        self.assertEqual(fmt_size(0), "0 B")
        self.assertEqual(fmt_size(128), "128 B")
        self.assertEqual(fmt_size(4300), "4.2 kB")
        self.assertEqual(fmt_size(1_400_000), "1.3 MB")


class TestTreeLines(unittest.TestCase):
    def test_hierarchy_and_ordering(self):
        items = [
            {"path": "src/main.rs", "type": "blob", "size": 1024},
            {"path": "src/parser/mod.rs", "type": "blob", "size": 512},
            {"path": "tests", "type": "tree"},
            {"path": "README.md", "type": "blob", "size": 520},
        ]
        lines = tree_to_lines(items)
        names = [l["name"] for l in lines]
        # Dirs sort before files at each level
        self.assertEqual(names[0], "src")
        self.assertIn("README.md", names)
        # branch glyph present on dir row
        self.assertTrue(all("connector" in l for l in lines))
        # sizes humanizable
        main_row = next(l for l in lines if l["name"] == "main.rs")
        self.assertEqual(main_row["size"], 1024)

    def test_max_lines_truncation(self):
        items = [{"path": f"f_{i}.py", "type": "blob", "size": i} for i in range(20)]
        lines = tree_to_lines(items, max_lines=10)
        self.assertLessEqual(len(lines), 10)
        self.assertEqual(lines[-1]["connector"], "truncated")


class TestCadenceSummary(unittest.TestCase):
    def test_surging(self):
        base = [1, 1, 1, 1, 2, 1, 1, 2, 1, 2, 1, 2]
        res = cadence_summary(base * 4 + [8, 9, 8, 10])
        self.assertIsNotNone(res)
        self.assertIn(res["momentum"], ("🚀 surging", "▲ accelerating"))
        self.assertEqual(res["best_week"], max(res["weeks"]))

    def test_cooling(self):
        hot = [10, 12, 11, 10] * 4 + [0, 1, 0, 0]
        res = cadence_summary(hot)
        self.assertEqual(res["momentum"], "▼ cooling")

    def test_empty_and_zero(self):
        self.assertIsNone(cadence_summary([]))
        self.assertIsNone(cadence_summary([0] * 52))


if __name__ == "__main__":
    unittest.main()
