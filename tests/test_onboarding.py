import unittest
from unittest.mock import patch
from gitsolve.onboarding import is_onboarding_needed

class TestOnboarding(unittest.TestCase):
    @patch("gitsolve.onboarding.load_config")
    def test_is_onboarding_needed_false(self, mock_load):
        mock_load.return_value = {"onboarded": True}
        self.assertFalse(is_onboarding_needed())

    @patch("gitsolve.onboarding.load_config")
    def test_is_onboarding_needed_true(self, mock_load):
        mock_load.return_value = {"onboarded": False}
        self.assertTrue(is_onboarding_needed())

        mock_load.return_value = {}
        self.assertTrue(is_onboarding_needed())

if __name__ == "__main__":
    unittest.main()
