import unittest
from gitsolve.animation import (
    render_meter,
    render_sparkline,
    render_language_bar,
    render_equalizer,
    render_pill,
    radar_pulse,
)

class TestAnimation(unittest.TestCase):
    def test_render_meter_boundaries(self):
        m0 = render_meter(0, 100, width=10, show_score=False)
        self.assertIn("▱" * 10, m0)

        m50 = render_meter(50, 100, width=10, show_score=False)
        self.assertIn("▰" * 5, m50)
        self.assertIn("▱" * 5, m50)

        m100 = render_meter(100, 100, width=10, show_score=False)
        self.assertIn("▰" * 10, m100)

    def test_render_sparkline(self):
        spark = render_sparkline([1, 2, 4, 8, 16])
        self.assertEqual(len(spark), 5)
        self.assertIn("█", spark)
        self.assertIn(" ", spark)

    def test_render_language_bar(self):
        langs = {"Rust": 8000, "Python": 2000}
        bar = render_language_bar(langs, width=20)
        self.assertIn("Rust 80%", bar)
        self.assertIn("Python 20%", bar)
        self.assertIn("█", bar)

    def test_render_equalizer(self):
        eq1 = render_equalizer(step=1, num_bars=6)
        self.assertEqual(len(eq1), 6)
        eq2 = render_equalizer(step=4, num_bars=6)
        self.assertEqual(len(eq2), 6)

    def test_render_pill(self):
        pill = render_pill("MYTHIC", bg_color="#F29265")
        self.assertIn("MYTHIC", pill)
        self.assertIn("#F29265", pill)

    def test_radar_pulse_context(self):
        # Ensure context manager completes cleanly without error
        with radar_pulse("Test animation pulse"):
            x = 1 + 1
        self.assertEqual(x, 2)

    def test_neural_pulse_context(self):
        # Ensure neural pulse context manager completes cleanly without error
        from gitsolve.animation import neural_pulse
        with neural_pulse("Test neural pulse"):
            y = 2 * 3
        self.assertEqual(y, 6)

if __name__ == "__main__":
    unittest.main()
