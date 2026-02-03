import logging
import unittest
from unittest.mock import patch

# Import the module we want to test
from s1ifr import get_path_from_base_safe


class TestGetPathFromBaseSafe(unittest.TestCase):
    """Unit tests for the get_path_from_base_safe.py module."""

    def test_get_safe_basename_from_fullpath_measu(self):
        """
        Should correctly extract the SAFE directory name from a full measurement path.
        """
        # --- Arrange ---
        measurement_path = "/archive/S1A_IW_GRDH_1SDV_20220101T120000_..._1234.SAFE/measurement/s1a-iw-grd-vv-....tiff"
        expected_basename = "S1A_IW_GRDH_1SDV_20220101T120000_..._1234.SAFE"

        # --- Act ---
        result = get_path_from_base_safe.get_safe_basename_from_fullpath_measu(
            measurement_path
        )

        # --- Assert ---
        self.assertEqual(result, expected_basename)

    @patch("s1ifr.get_path_from_base_safe.glob.glob")
    @patch("s1ifr.get_path_from_base_safe.which_archive_dir")
    def test_get_path_from_base_safe_simple_case(
        self, mock_which_archive_dir, mock_glob
    ):
        """
        Should return the full path for a simple basename without wildcards.
        """
        # --- Arrange ---
        mock_which_archive_dir.return_value = "/fake/archive/path"
        safe_name = "S1A_IW_SLC__1SDV_..._939A.SAFE"
        expected_path = "/fake/archive/path/S1A_IW_SLC__1SDV_..._939A.SAFE"

        # --- Act ---
        result = get_path_from_base_safe.get_path_from_base_safe(safe_name)

        # --- Assert ---
        self.assertEqual(result, expected_path)
        mock_which_archive_dir.assert_called_once_with(
            safe_name, archive_name="datawork"
        )
        mock_glob.assert_not_called()  # Glob should not be called if there's no wildcard

    @patch("s1ifr.get_path_from_base_safe.glob.glob")
    @patch("s1ifr.get_path_from_base_safe.which_archive_dir")
    def test_get_path_with_wildcard_finds_match(
        self, mock_which_archive_dir, mock_glob
    ):
        """
        Should return the first matched file when a wildcard is used and a file is found.
        """
        # --- Arrange ---
        mock_which_archive_dir.return_value = "/fake/archive/path"
        # Simulate glob finding one or more files
        mock_glob.return_value = [
            "/fake/archive/path/S1A_IW_SLC__1SDV_..._REAL_MATCH.SAFE",
            "/another/file",
        ]
        wildcard_name = "S1A_IW_SLC_*.SAFE"

        # --- Act ---
        result = get_path_from_base_safe.get_path_from_base_safe(wildcard_name)

        # --- Assert ---
        self.assertEqual(
            result, "/fake/archive/path/S1A_IW_SLC__1SDV_..._REAL_MATCH.SAFE"
        )
        mock_glob.assert_called_once_with(
            f"/fake/archive/path/{wildcard_name}"
        )

    @patch("s1ifr.get_path_from_base_safe.glob.glob")
    @patch("s1ifr.get_path_from_base_safe.which_archive_dir")
    def test_get_path_with_wildcard_finds_no_match(
        self, mock_which_archive_dir, mock_glob
    ):
        """
        Should return the original path with the wildcard if no match is found.
        """
        # --- Arrange ---
        mock_which_archive_dir.return_value = "/fake/archive/path"
        # Simulate glob finding no files
        mock_glob.return_value = []
        wildcard_name = "S1A_IW_SLC_*.SAFE"
        expected_path_with_wildcard = "/fake/archive/path/S1A_IW_SLC_*.SAFE"

        # --- Act ---
        result = get_path_from_base_safe.get_path_from_base_safe(wildcard_name)
        # Suppress the expected warning log message during this test
        # with self.assertLogs('s1ifr.get_path_from_base_safe', level='WARNING') as cm:
        #     result = get_path_from_base_safe.get_path_from_base_safe(wildcard_name)
        #     # Check that the correct warning was logged
        #     self.assertIn(f"No file found matching pattern: {expected_path_with_wildcard}", cm.output[0])

        # --- Assert ---
        self.assertEqual(result, expected_path_with_wildcard)


if __name__ == "__main__":
    unittest.main()
