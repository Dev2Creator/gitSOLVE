import unittest
from typer.testing import CliRunner
from gitsolve.cli import app

runner = CliRunner()

class TestCLI(unittest.TestCase):
    def test_version_command(self):
        result = runner.invoke(app, ["version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("gitSOLVE", result.output)
        self.assertIn("v0.3.0", result.output)

    def test_help_command(self):
        result = runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("radar", result.output)
        self.assertIn("xray", result.output)
        self.assertIn("forks", result.output)
        self.assertIn("vault", result.output)
        self.assertIn("fresh", result.output)
        self.assertIn("compare", result.output)
        self.assertIn("author", result.output)
        self.assertIn("velocity", result.output)
        self.assertIn("limits", result.output)
        self.assertIn("readme", result.output)
        self.assertIn("tree", result.output)
        self.assertIn("commits", result.output)
        self.assertIn("export", result.output)
        self.assertIn("presets", result.output)

    def test_vault_json_output(self):
        result = runner.invoke(app, ["vault", "--json"])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.output.strip().startswith("[") or result.output.strip().startswith("{"))

    def test_presets_command(self):
        result = runner.invoke(app, ["presets"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("CURATED ECOSYSTEM PRESETS", result.output)
        self.assertIn("rust", result.output)
        self.assertIn("python", result.output)

    def test_export_markdown_command(self):
        result = runner.invoke(app, ["export", "--format", "markdown", "--output", "/tmp/cli_test_portfolio.md"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Vault portfolio exported", result.output)

if __name__ == "__main__":
    unittest.main()
