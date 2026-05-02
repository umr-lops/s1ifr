# tests/test_sentinel1_pieuvre.py
import os
import tempfile
import unittest
from unittest.mock import patch

from s1ifr import sentinel1_pieuvre

CONFIG_YAML = """
product_info:
  modes: ["SM", "WV", "IW", "EW"]
  types: ["OCN_", "GRDH", "SLC_", "GRDM", "GRDF", "RAW_"]
  extensions:
    L1: "tiff"
    L2: "nc"

satellites:
  longnames:
    S1A: "sentinel-1a"
    S1B: "sentinel-1b"
    S1C: "sentinel-1c"
    S1D: "sentinel-1d"
  acronyms:
    sentinel-1a: "S1A"
    sentinel-1b: "S1B"
    sentinel-1c: "S1C"
    sentinel-1d: "S1D"

paths:
  datawork:
    project_cache: "/fake/cache/"
    project_main: "/fake/main/"
    archive_esa: "/fake/archive/esa"
    archive_esa_cache: "/fake/cache/esa"
    workspace: "/fake/workspace"
    quarantine: "/fake/quarantine"
    dir_outs_l1c: ["/fake/l1c"]
    dir_outs_l1b: ["/fake/l1b"]
    dir_out_l2wav: ["/fake/l2wav"]
  scale:
    workbench: "/fake/scale/"
    archive_esa: "/fake/scale/esa"
    workspace: "/fake/scale/workspace"
  scratch:
    satwave: "/fake/scratch/"

DEFAULT_VERSIONS_L1B: ["A23"]
DEFAULT_VERSIONS_L1C: ["B09"]
DEFAULT_VERSIONS_L2WAV: ["E11"]
"""


class TestFinalizeArchiving(unittest.TestCase):
    """Tests for the finalize_archiving function."""

    def setUp(self):
        """Write a temporary config file reused across all tests in this class."""
        self.config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        )
        self.config_file.write(CONFIG_YAML)
        self.config_file.close()
        self.config_path = self.config_file.name

    def tearDown(self):
        os.unlink(self.config_path)

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
        mock_safe_checker.return_value = False  # SAFE is corrupted

        result = sentinel1_pieuvre.finalize_archiving(
            archive_dir="/fake/archive",
            unzipped_safe="/fake/spool/product.SAFE",
            final_place="/fake/archive/product.SAFE",
            ziptype=".zip",
            archive_name="my_archive",
            config_path=self.config_path,
        )
        print(result)
        mock_quarantine.assert_called_once()
