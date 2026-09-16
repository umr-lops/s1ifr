import os
import unittest
from unittest.mock import mock_open, patch

import s1ifr
from s1ifr import utils


class TestUtils(unittest.TestCase):
    """Unit tests for the s1ifr.utils module."""

    @patch("s1ifr.utils.yaml.load")
    @patch("s1ifr.utils.open", new_callable=mock_open)
    @patch("s1ifr.utils.os.path.exists")
    def test_load_config_uses_local_if_exists(
        self, mock_exists, mock_file, mock_yaml_load
    ):
        """
        Should load 'localconfig.yml' when it exists.
        """
        # --- Arrange ---
        # Simulate that localconfig.yml exists
        mock_exists.return_value = True
        # Define what the mock yaml.load should return
        expected_config = {"source": "local"}
        mock_yaml_load.return_value = expected_config

        s1ifr_path = os.path.dirname(s1ifr.__file__)
        expected_path = os.path.join(s1ifr_path, "localconfig.yml")

        # --- Act ---
        config = utils.load_config()

        # --- Assert ---
        # Check that os.path.exists was called with the correct path
        mock_exists.assert_called_once_with(expected_path)
        # Check that open was called with the local config path
        mock_file.assert_called_once_with(expected_path)
        # Check that the loaded config is the one we defined
        self.assertEqual(config, expected_config)

    @patch("s1ifr.utils.yaml.load")
    @patch("s1ifr.utils.open", new_callable=mock_open)
    @patch("s1ifr.utils.os.path.exists")
    def test_load_config_falls_back_to_default(
        self, mock_exists, mock_file, mock_yaml_load
    ):
        """
        Should fall back to loading 'config.yml' when 'localconfig.yml' does not exist.
        """
        # --- Arrange ---
        # Simulate that localconfig.yml does NOT exist
        mock_exists.return_value = False
        expected_config = {"source": "default"}
        mock_yaml_load.return_value = expected_config

        s1ifr_path = os.path.dirname(s1ifr.__file__)
        expected_local_path = os.path.join(s1ifr_path, "localconfig.yml")
        expected_default_path = os.path.join(s1ifr_path, "config.yml")

        # --- Act ---
        config = utils.load_config()

        # --- Assert ---
        mock_exists.assert_called_once_with(expected_local_path)
        # Check that open was called with the default config path
        mock_file.assert_called_once_with(expected_default_path)
        self.assertEqual(config, expected_config)

    def test_give_me_level_from_type(self):
        """
        Should return the correct product level for different type formats.
        """
        self.assertEqual(utils.give_me_level_from_type("SM_RAW__2S"), "L0")
        self.assertEqual(utils.give_me_level_from_type("IW_OCN__2S"), "L2")
        self.assertEqual(utils.give_me_level_from_type("IW_GRDH_1S"), "L1")
        self.assertEqual(utils.give_me_level_from_type("EW_SLC__1S"), "L1")

    @patch("s1ifr.utils.load_config")
    def test_dir_data(self, mock_load_config):
        """
        Should construct the correct data path using the loaded configuration.
        """
        # --- Arrange ---
        # Create a fake configuration dictionary to be returned by the mock
        fake_config = {
            "satellites": {
                "longnames": {"S1A": "sentinel-1a", "S1B": "sentinel-1b"}
            },
            "paths": {"datarmor": {"archive_esa": "/test/archive/path"}},
        }
        # Tell the mock to return our fake config when called
        mock_load_config.return_value = fake_config

        # --- Act ---
        result_path = utils.dir_data("S1A")

        # --- Assert ---
        # Check that our function correctly constructed the path
        expected_path = "/test/archive/path/sentinel-1a"
        self.assertEqual(result_path, expected_path)
        # Ensure that load_config was actually called
        mock_load_config.assert_called_once()


if __name__ == "__main__":
    unittest.main()
