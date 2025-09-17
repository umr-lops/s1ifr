# tests/test_sentinel1_pieuvre.py
import unittest
from unittest.mock import patch

# The module to be tested
from s1ifr import sentinel1_pieuvre


class TestFinalizeArchiving(unittest.TestCase):
    """Tests for the finalize_archiving function."""

    @patch("s1ifr.sentinel1_pieuvre.os.path.isdir", return_value=False)
    @patch("s1ifr.sentinel1_pieuvre.os.remove")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists", return_value=True)
    @patch("s1ifr.sentinel1_pieuvre.quarantine_ticket")
    @patch("s1ifr.sentinel1_pieuvre.subprocess.run")
    @patch("s1ifr.sentinel1_pieuvre.safe_checker")
    @patch("s1ifr.sentinel1_pieuvre.getpass.getuser", return_value="testuser")
    def test_finalize_archiving_corrupted_safe(
        self,
        mock_getuser,
        mock_safe_checker,
        mock_subprocess_run,
        mock_quarantine,
        mock_exists,
        mock_remove,
        mock_isdir,
    ):
        """Test when safe_checker finds a corrupted SAFE, it gets quarantined."""
        # Arrange
        mock_safe_checker.return_value = False  # SAFE is corrupted

        # Act
        result = sentinel1_pieuvre.finalize_archiving(
            archive_dir="/fake/archive",
            unzipped_safe="/fake/spool/product.SAFE",
            final_place="/fake/archive/product.SAFE",
            ziptype=".zip",
            archive_name="my_archive",
        )
        print(result)
