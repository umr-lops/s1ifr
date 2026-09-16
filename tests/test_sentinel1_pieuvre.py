# tests/test_sentinel1_pieuvre.py
import argparse
import datetime
import os
import shutil
import subprocess
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
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
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
        final_place = "/fake/archive/product.SAFE"
        unzipped_safe = "/fake/spool/product.SAFE"

        # final_place must NOT exist (so we don't take the ALREADY branch);
        # the unzipped safe / original archive DO exist.
        mock_exists.side_effect = lambda path: path != final_place

        result = sentinel1_pieuvre.finalize_archiving(
            archive_dir="/fake/archive",
            unzipped_safe=unzipped_safe,
            final_place=final_place,
            ziptype=".zip",
            archive_name="my_archive",
            config_path=self.config_path,
        )
        mock_quarantine.assert_called_once()
        self.assertEqual(result, sentinel1_pieuvre.QUARANTINED)


class TestSortOneSafe(unittest.TestCase):
    """Tests for the sort_one_safe function."""

    def setUp(self):
        """Create temporary test environment."""
        self.config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        )
        self.config_file.write(CONFIG_YAML)
        self.config_file.close()
        self.config_path = self.config_file.name

        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.spool_dir = os.path.join(self.temp_dir, "spool")
        self.archive_dir = os.path.join(self.temp_dir, "archive")
        os.makedirs(self.spool_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)

    def tearDown(self):
        os.unlink(self.config_path)
        shutil.rmtree(self.temp_dir)

    @patch("s1ifr.sentinel1_pieuvre.which_archive_dir")
    @patch("s1ifr.sentinel1_pieuvre.which_spool_dir")
    @patch("s1ifr.sentinel1_pieuvre.product_is_present_at_ifremer")
    @patch("s1ifr.sentinel1_pieuvre.safe_checker")
    @patch("s1ifr.sentinel1_pieuvre.finalize_archiving")
    @patch("s1ifr.sentinel1_pieuvre.os.system")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getsize")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getctime")
    @patch("s1ifr.sentinel1_pieuvre.os.makedirs")
    @patch("s1ifr.sentinel1_pieuvre.os.chdir")
    @patch("s1ifr.sentinel1_pieuvre.time.sleep")
    def test_sort_one_safe_tar_success(
        self,
        mock_sleep,
        mock_chdir,
        mock_makedirs,
        mock_getctime,
        mock_getsize,
        mock_exists,
        mock_system,
        mock_finalize,
        mock_safe_checker,
        mock_product_present,
        mock_spool_dir,
        mock_archive_dir,
    ):
        """Test successful processing of a .tar SAFE file."""
        safe_name = "S1A_IW_GRDH_1SDV_20200101T000000_20200101T000025_030000_030000_0000.SAFE"
        safe_path = os.path.join(self.spool_dir, f"{safe_name}.tar")

        # Mock file operations
        mock_exists.return_value = True
        mock_getsize.side_effect = [1024, 1024]  # Same size = file stable
        mock_getctime.return_value = (
            datetime.datetime.now() - datetime.timedelta(hours=1)
        ).timestamp()
        mock_system.return_value = 0

        mock_archive_dir.return_value = self.archive_dir
        mock_spool_dir.return_value = self.spool_dir
        mock_product_present.return_value = (True, None, None)
        mock_safe_checker.return_value = True
        mock_finalize.return_value = sentinel1_pieuvre.NORMAL

        result, cpt = sentinel1_pieuvre.sort_one_safe(
            full_path_safe=safe_path,
            config_path=self.config_path,
            security_second=0,
            dryrun=False,
        )

        self.assertEqual(result, sentinel1_pieuvre.NORMAL)
        mock_finalize.assert_called_once()

    @patch("s1ifr.sentinel1_pieuvre.which_archive_dir")
    @patch("s1ifr.sentinel1_pieuvre.product_is_present_at_ifremer")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.remove_safe_from_disk")
    def test_sort_one_safe_already_exists(
        self, mock_remove, mock_exists, mock_product_present, mock_archive_dir
    ):
        """Test when product already exists at destination."""
        safe_name = "S1A_IW_GRDH_1SDV_20200101T000000_20200101T000025_030000_030000_0000.SAFE"
        safe_path = os.path.join(self.spool_dir, f"{safe_name}.SAFE")

        mock_exists.return_value = True
        mock_archive_dir.return_value = self.archive_dir
        mock_product_present.return_value = (False, None, None)

        result, cpt = sentinel1_pieuvre.sort_one_safe(
            full_path_safe=safe_path,
            config_path=self.config_path,
            security_second=0,
            dryrun=False,
        )

        self.assertEqual(result, sentinel1_pieuvre.ALREADY)
        mock_remove.assert_called_once()

    @patch("s1ifr.sentinel1_pieuvre.which_archive_dir")
    @patch("s1ifr.sentinel1_pieuvre.which_spool_dir")
    @patch("s1ifr.sentinel1_pieuvre.product_is_present_at_ifremer")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getsize")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getctime")
    @patch("s1ifr.sentinel1_pieuvre.os.makedirs")
    @patch("s1ifr.sentinel1_pieuvre.time.sleep")
    def test_sort_one_safe_too_recent(
        self,
        mock_sleep,
        mock_makedirs,
        mock_getctime,
        mock_getsize,
        mock_exists,
        mock_product_present,
        mock_spool_dir,
        mock_archive_dir,
    ):
        """Test when file is too recent (security_second not met)."""
        safe_name = "S1A_IW_GRDH_1SDV_20200101T000000_20200101T000025_030000_030000_0000.SAFE"
        safe_path = os.path.join(self.spool_dir, f"{safe_name}.SAFE")

        mock_exists.return_value = True
        mock_getsize.side_effect = [1024, 1024]
        # File created 100 seconds ago
        mock_getctime.return_value = (
            datetime.datetime.now() - datetime.timedelta(seconds=100)
        ).timestamp()

        mock_archive_dir.return_value = self.archive_dir
        mock_spool_dir.return_value = self.spool_dir
        mock_product_present.return_value = (True, None, None)

        # Security threshold is 3600 seconds, file is only 100 seconds old
        result, cpt = sentinel1_pieuvre.sort_one_safe(
            full_path_safe=safe_path,
            config_path=self.config_path,
            security_second=3600,
            dryrun=False,
        )

        self.assertEqual(result, sentinel1_pieuvre.TOORECENT)

    @patch("s1ifr.sentinel1_pieuvre.which_archive_dir")
    @patch("s1ifr.sentinel1_pieuvre.product_is_present_at_ifremer")
    def test_sort_one_safe_file_not_found(
        self, mock_product_present, mock_archive_dir
    ):
        """Test when file doesn't exist."""
        safe_path = "/fake/path/does/not/exist.SAFE"

        with patch(
            "s1ifr.sentinel1_pieuvre.os.path.exists", return_value=False
        ):
            result, cpt = sentinel1_pieuvre.sort_one_safe(
                full_path_safe=safe_path,
                config_path=self.config_path,
                security_second=0,
                dryrun=False,
            )

            self.assertEqual(result, sentinel1_pieuvre.UNEXISTANT)

    @patch("s1ifr.sentinel1_pieuvre.which_archive_dir")
    @patch("s1ifr.sentinel1_pieuvre.which_spool_dir")
    @patch("s1ifr.sentinel1_pieuvre.product_is_present_at_ifremer")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getsize")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getctime")
    @patch("s1ifr.sentinel1_pieuvre.os.makedirs")
    @patch("s1ifr.sentinel1_pieuvre.time.sleep")
    def test_sort_one_safe_dryrun(
        self,
        mock_sleep,
        mock_makedirs,
        mock_getctime,
        mock_getsize,
        mock_exists,
        mock_product_present,
        mock_spool_dir,
        mock_archive_dir,
    ):
        """Test dryrun mode."""
        safe_name = "S1A_IW_GRDH_1SDV_20200101T000000_20200101T000025_030000_030000_0000.SAFE"
        safe_path = os.path.join(self.spool_dir, f"{safe_name}.tar")

        mock_exists.return_value = True
        mock_getsize.side_effect = [1024, 1024]
        mock_getctime.return_value = (
            datetime.datetime.now() - datetime.timedelta(hours=1)
        ).timestamp()

        mock_archive_dir.return_value = self.archive_dir
        mock_spool_dir.return_value = self.spool_dir
        mock_product_present.return_value = (True, None, None)

        # In dryrun mode, we should not actually do anything
        result, cpt = sentinel1_pieuvre.sort_one_safe(
            full_path_safe=safe_path,
            config_path=self.config_path,
            security_second=0,
            dryrun=True,
        )

        # Since we're mocking everything, the function should return the default
        self.assertIsInstance(result, str)

    @patch("s1ifr.sentinel1_pieuvre.which_archive_dir")
    @patch("s1ifr.sentinel1_pieuvre.which_spool_dir")
    @patch("s1ifr.sentinel1_pieuvre.product_is_present_at_ifremer")
    @patch("s1ifr.sentinel1_pieuvre.quarantine_ticket")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getsize")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getctime")
    @patch("s1ifr.sentinel1_pieuvre.os.makedirs")
    @patch("s1ifr.sentinel1_pieuvre.os.chdir")
    @patch("s1ifr.sentinel1_pieuvre.time.sleep")
    @patch("s1ifr.sentinel1_pieuvre.os.system")
    def test_sort_one_safe_corrupted_tar(
        self,
        mock_system,
        mock_sleep,
        mock_chdir,
        mock_makedirs,
        mock_getctime,
        mock_getsize,
        mock_exists,
        mock_quarantine,
        mock_product_present,
        mock_spool_dir,
        mock_archive_dir,
    ):
        """Test corrupted tar file gets quarantined."""
        safe_name = "S1A_IW_GRDH_1SDV_20200101T000000_20200101T000025_030000_030000_0000.SAFE"
        safe_path = os.path.join(self.spool_dir, f"{safe_name}.tar")

        mock_exists.return_value = True
        mock_getsize.side_effect = [1024, 1024]
        mock_getctime.return_value = (
            datetime.datetime.now() - datetime.timedelta(hours=1)
        ).timestamp()

        mock_archive_dir.return_value = self.archive_dir
        mock_spool_dir.return_value = self.spool_dir
        mock_product_present.return_value = (True, None, None)

        # Mock os.system to return non-zero (fail)
        mock_system.return_value = 1

        result, cpt = sentinel1_pieuvre.sort_one_safe(
            full_path_safe=safe_path,
            config_path=self.config_path,
            security_second=0,
            dryrun=False,
        )

        self.assertEqual(result, sentinel1_pieuvre.QUARANTINED)
        mock_quarantine.assert_called_once()


class TestFinalizeArchivingAdditional(unittest.TestCase):
    """Additional tests for finalize_archiving function."""

    def setUp(self):
        """Create temporary test environment."""
        self.config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        )
        self.config_file.write(CONFIG_YAML)
        self.config_file.close()
        self.config_path = self.config_file.name

        self.temp_dir = tempfile.mkdtemp()
        self.archive_dir = os.path.join(self.temp_dir, "archive")
        self.spool_dir = os.path.join(self.temp_dir, "spool")
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.spool_dir, exist_ok=True)

        self.safe_name = "S1A_IW_GRDH_1SDV_20200101T000000_20200101T000025_030000_030000_0000.SAFE"
        self.unzipped_safe = os.path.join(self.spool_dir, self.safe_name)
        self.final_place = os.path.join(self.archive_dir, self.safe_name)

        # Create a mock SAFE directory
        os.makedirs(self.unzipped_safe, exist_ok=True)

        # Create a mock tar file
        self.tar_path = self.unzipped_safe + ".tar"
        with open(self.tar_path, "w") as f:
            f.write("mock tar content")

    def tearDown(self):
        os.unlink(self.config_path)
        shutil.rmtree(self.temp_dir)

    @patch("s1ifr.sentinel1_pieuvre.safe_checker")
    @patch("s1ifr.sentinel1_pieuvre.subprocess.check_output")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.os.remove")
    @patch("s1ifr.sentinel1_pieuvre.os.path.isdir")
    def test_finalize_archiving_success_tar(
        self,
        mock_isdir,
        mock_remove,
        mock_exists,
        mock_subprocess,
        mock_safe_checker,
    ):
        """Test successful archiving of .tar file."""
        mock_safe_checker.return_value = True
        # check_output should return b'' (success) for both mv and chmod
        mock_subprocess.return_value = b""
        mock_isdir.return_value = False

        # Mock exists: final_place doesn't exist, unzipped_safe exists, tar exists
        def exists_side_effect(path):
            if path == self.final_place:
                return False
            if path == self.unzipped_safe:
                return True
            if path == self.unzipped_safe + ".tar":
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        result = sentinel1_pieuvre.finalize_archiving(
            archive_dir=self.archive_dir,
            unzipped_safe=self.unzipped_safe,
            final_place=self.final_place,
            ziptype=".tar",
            archive_name="datawork",
            config_path=self.config_path,
        )

        self.assertEqual(result, sentinel1_pieuvre.NORMAL)

    @patch("s1ifr.sentinel1_pieuvre.safe_checker")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.remove_safe_from_disk")
    @patch("s1ifr.sentinel1_pieuvre.quarantine_ticket")
    def test_finalize_archiving_already_exists(
        self, mock_quarantine, mock_remove, mock_exists, mock_safe_checker
    ):
        """Test when final_place already exists."""
        mock_safe_checker.return_value = True
        # final_place exists
        mock_exists.return_value = True

        result = sentinel1_pieuvre.finalize_archiving(
            archive_dir=self.archive_dir,
            unzipped_safe=self.unzipped_safe,
            final_place=self.final_place,
            ziptype=".tar",
            archive_name="datawork",
            config_path=self.config_path,
        )

        self.assertEqual(result, sentinel1_pieuvre.ALREADY)
        mock_remove.assert_called_once_with(self.unzipped_safe)
        mock_quarantine.assert_not_called()

    @patch("s1ifr.sentinel1_pieuvre.safe_checker")
    @patch("s1ifr.sentinel1_pieuvre.subprocess.check_output")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.os.remove")
    @patch("s1ifr.sentinel1_pieuvre.os.path.isdir")
    def test_finalize_archiving_chmod_failure(
        self,
        mock_isdir,
        mock_remove,
        mock_exists,
        mock_subprocess,
        mock_safe_checker,
    ):
        """Test when chmod operation fails."""
        mock_safe_checker.return_value = True
        mock_isdir.return_value = False
        # Make mv succeed (b''), but chmod fail (CalledProcessError)
        mock_subprocess.side_effect = [
            b"",  # mv succeeds
            subprocess.CalledProcessError(1, "chmod"),  # chmod fails
        ]

        # Mock exists: final_place doesn't exist, unzipped_safe exists, tar exists
        def exists_side_effect(path):
            if path == self.final_place:
                return False
            if path == self.unzipped_safe:
                return True
            if path == self.unzipped_safe + ".tar":
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        result = sentinel1_pieuvre.finalize_archiving(
            archive_dir=self.archive_dir,
            unzipped_safe=self.unzipped_safe,
            final_place=self.final_place,
            ziptype=".tar",
            archive_name="datawork",
            config_path=self.config_path,
        )

        self.assertEqual(result, sentinel1_pieuvre.FAILED)

    @patch("s1ifr.sentinel1_pieuvre.safe_checker")
    @patch("s1ifr.sentinel1_pieuvre.subprocess.check_output")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.os.remove")
    @patch("s1ifr.sentinel1_pieuvre.os.path.isdir")
    def test_finalize_archiving_mv_failure(
        self,
        mock_isdir,
        mock_remove,
        mock_exists,
        mock_subprocess,
        mock_safe_checker,
    ):
        """Test when mv operation fails."""
        mock_safe_checker.return_value = True
        mock_isdir.return_value = False
        # mv fails
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "mv")

        # Mock exists: final_place doesn't exist, unzipped_safe exists, tar exists
        def exists_side_effect(path):
            if path == self.final_place:
                return False
            if path == self.unzipped_safe:
                return True
            if path == self.unzipped_safe + ".tar":
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        result = sentinel1_pieuvre.finalize_archiving(
            archive_dir=self.archive_dir,
            unzipped_safe=self.unzipped_safe,
            final_place=self.final_place,
            ziptype=".tar",
            archive_name="datawork",
            config_path=self.config_path,
        )

        self.assertEqual(result, sentinel1_pieuvre.FAILED)

    @patch("s1ifr.sentinel1_pieuvre.safe_checker")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.quarantine_ticket")
    @patch("s1ifr.sentinel1_pieuvre.os.remove")
    @patch("s1ifr.sentinel1_pieuvre.os.path.isdir")
    @patch("s1ifr.sentinel1_pieuvre.shutil.rmtree")
    def test_finalize_archiving_corrupted_safe_zip(
        self,
        mock_rmtree,
        mock_isdir,
        mock_remove,
        mock_quarantine,
        mock_exists,
        mock_safe_checker,
    ):
        """Test corrupted zip SAFE gets quarantined."""
        mock_safe_checker.return_value = False
        mock_isdir.return_value = False

        # final_place must NOT exist so the corruption branch is reached
        # instead of the ALREADY branch.
        mock_exists.side_effect = lambda path: path != self.final_place

        result = sentinel1_pieuvre.finalize_archiving(
            archive_dir=self.archive_dir,
            unzipped_safe=self.unzipped_safe,
            final_place=self.final_place,
            ziptype=".zip",
            archive_name="datawork",
            config_path=self.config_path,
        )

        self.assertEqual(result, sentinel1_pieuvre.QUARANTINED)
        mock_quarantine.assert_called_once_with(
            self.unzipped_safe, "datawork", config_path=self.config_path
        )


class TestMainFunction(unittest.TestCase):
    """Tests for the main function."""

    def setUp(self):
        self.config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        )
        self.config_file.write(CONFIG_YAML)
        self.config_file.close()
        self.config_path = self.config_file.name

    def tearDown(self):
        os.unlink(self.config_path)

    @patch("s1ifr.sentinel1_pieuvre.sort_one_safe")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_basic(self, mock_args, mock_sort):
        """Test main function with basic arguments."""
        mock_args.return_value = argparse.Namespace(
            safe="/fake/path/S1A_IW_GRDH.SAFE",
            archivename="datawork",
            config_path=self.config_path,
            verbose=False,
            dryrun=False,
        )
        mock_sort.return_value = (sentinel1_pieuvre.NORMAL, 0)

        sentinel1_pieuvre.main()
        mock_sort.assert_called_once_with(
            "/fake/path/S1A_IW_GRDH.SAFE",
            other_archive="datawork",
            security_second=0,
            dryrun=False,
            config_path=self.config_path,
        )

    @patch("s1ifr.sentinel1_pieuvre.sort_one_safe")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_dryrun(self, mock_args, mock_sort):
        """Test main function with dryrun option."""
        mock_args.return_value = argparse.Namespace(
            safe="/fake/path/S1A_IW_GRDH.SAFE",
            archivename="scale",
            config_path=self.config_path,
            verbose=True,
            dryrun=True,
        )
        mock_sort.return_value = (sentinel1_pieuvre.NORMAL, 0)

        sentinel1_pieuvre.main()
        mock_sort.assert_called_once_with(
            "/fake/path/S1A_IW_GRDH.SAFE",
            other_archive="scale",
            security_second=0,
            dryrun=True,
            config_path=self.config_path,
        )


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        self.config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        )
        self.config_file.write(CONFIG_YAML)
        self.config_file.close()
        self.config_path = self.config_file.name

    def tearDown(self):
        os.unlink(self.config_path)

    def test_sort_one_safe_with_trailing_slash(self):
        """Test that trailing slash is handled correctly."""
        safe_path = "/fake/path/S1A_IW_GRDH.SAFE/"

        with patch(
            "s1ifr.sentinel1_pieuvre.os.path.exists", return_value=False
        ):
            result, _ = sentinel1_pieuvre.sort_one_safe(
                full_path_safe=safe_path,
                config_path=self.config_path,
                security_second=0,
                dryrun=False,
            )
            self.assertEqual(result, sentinel1_pieuvre.UNEXISTANT)

    @patch("s1ifr.sentinel1_pieuvre.which_archive_dir")
    @patch("s1ifr.sentinel1_pieuvre.which_spool_dir")
    @patch("s1ifr.sentinel1_pieuvre.product_is_present_at_ifremer")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getsize")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getctime")
    @patch("s1ifr.sentinel1_pieuvre.os.makedirs")
    @patch("s1ifr.sentinel1_pieuvre.os.chdir")
    @patch("s1ifr.sentinel1_pieuvre.time.sleep")
    @patch("s1ifr.sentinel1_pieuvre.subprocess.check_output")
    @patch("s1ifr.sentinel1_pieuvre.quarantine_ticket")
    @patch("s1ifr.sentinel1_pieuvre.safe_checker")
    def test_sort_one_safe_zip_unzip_failure(
        self,
        mock_safe_checker,
        mock_quarantine,
        mock_check_output,
        mock_sleep,
        mock_chdir,
        mock_makedirs,
        mock_getctime,
        mock_getsize,
        mock_exists,
        mock_product_present,
        mock_spool_dir,
        mock_archive_dir,
    ):
        """Test zip extraction failure."""
        safe_name = "S1A_IW_GRDH_1SDV_20200101T000000_20200101T000025_030000_030000_0000.SAFE"
        safe_path = os.path.join("/fake/spool", f"{safe_name}.zip")

        # Only the original .zip exists on disk; nothing produced by the
        # (failed) unzip exists — this is what should drive the quarantine path.
        mock_exists.side_effect = lambda path: path == safe_path

        mock_getsize.side_effect = [1024, 1024]
        mock_getctime.return_value = (
            datetime.datetime.now() - datetime.timedelta(hours=1)
        ).timestamp()
        mock_safe_checker.return_value = False  # irrelevant here, but harmless

        mock_archive_dir.return_value = "/fake/archive"
        mock_spool_dir.return_value = "/fake/spool"
        mock_product_present.return_value = (True, None, None)

        # Mock unzip to fail with CalledProcessError
        mock_check_output.side_effect = subprocess.CalledProcessError(
            1, "unzip"
        )

        result, _ = sentinel1_pieuvre.sort_one_safe(
            full_path_safe=safe_path,
            config_path=self.config_path,
            security_second=0,
            dryrun=False,
        )

        # The function should quarantine the file
        self.assertEqual(result, sentinel1_pieuvre.QUARANTINED)
        mock_quarantine.assert_called_once()

    def test_sort_one_safe_without_extension(self):
        """Test when SAFE doesn't have proper extension."""
        safe_path = "/fake/spool/some_file_without_extension"

        with patch(
            "s1ifr.sentinel1_pieuvre.os.path.exists", return_value=False
        ):
            result, _ = sentinel1_pieuvre.sort_one_safe(
                full_path_safe=safe_path,
                config_path=self.config_path,
                security_second=0,
                dryrun=False,
            )
            self.assertEqual(result, sentinel1_pieuvre.UNEXISTANT)

    @patch("s1ifr.sentinel1_pieuvre.which_archive_dir")
    @patch("s1ifr.sentinel1_pieuvre.which_spool_dir")
    @patch("s1ifr.sentinel1_pieuvre.product_is_present_at_ifremer")
    @patch("s1ifr.sentinel1_pieuvre.safe_checker")
    @patch("s1ifr.sentinel1_pieuvre.os.path.exists")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getsize")
    @patch("s1ifr.sentinel1_pieuvre.os.path.getctime")
    @patch("s1ifr.sentinel1_pieuvre.os.makedirs")
    @patch("s1ifr.sentinel1_pieuvre.time.sleep")
    @patch("s1ifr.sentinel1_pieuvre.finalize_archiving")
    def test_sort_one_safe_sen3_extension(
        self,
        mock_finalize,
        mock_sleep,
        mock_makedirs,
        mock_getctime,
        mock_getsize,
        mock_exists,
        mock_safe_checker,
        mock_product_present,
        mock_spool_dir,
        mock_archive_dir,
    ):
        """Test handling of SEN3 files."""
        safe_name = "S3A_SL_1_RBT_20200101T000000_20200101T000025_030000_030000_0000.SEN3"
        safe_path = os.path.join("/fake/spool", safe_name)

        mock_exists.return_value = True
        mock_getsize.side_effect = [1024, 1024]
        mock_getctime.return_value = (
            datetime.datetime.now() - datetime.timedelta(hours=1)
        ).timestamp()

        mock_archive_dir.return_value = "/fake/archive"
        mock_spool_dir.return_value = "/fake/spool"
        mock_product_present.return_value = (True, None, None)
        mock_safe_checker.return_value = True
        mock_finalize.return_value = sentinel1_pieuvre.NORMAL

        result, _ = sentinel1_pieuvre.sort_one_safe(
            full_path_safe=safe_path,
            config_path=self.config_path,
            security_second=0,
            dryrun=False,
        )

        self.assertEqual(result, sentinel1_pieuvre.NORMAL)
        mock_finalize.assert_called_once()
