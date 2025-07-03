import datetime
import unittest
from unittest.mock import mock_open, patch

# Import the module we want to test
from s1ifr import produce_list_file_S1


class TestProduceListFileS1(unittest.TestCase):
    """Unit tests for the produce_list_file_S1 module."""

    # We patch 'load_config' at the class level because it's used by the module on import.
    # This ensures all tests run with a consistent, fake configuration.
    @classmethod
    def setUpClass(cls):
        cls.mock_config = {
            "product_info": {"extensions": {"L1": "tiff", "L2": "nc"}},
            "satellites": {"acronyms": {"S1A": "sentinel-1a"}},
            "paths": {"archives": {"datawork": "/archive/datawork"}},
        }
        # The patch needs to target where the object is *looked up*, which is in the module under test.
        cls.patcher = patch("s1ifr.produce_list_file_S1.conf", cls.mock_config)
        cls.patcher.start()
        # Also patch the imported dictionary directly if needed, though patching conf is better
        produce_list_file_S1.ADDITIONAL_ARCHIVES = cls.mock_config["paths"][
            "archives"
        ]
        produce_list_file_S1.sats_acro = cls.mock_config["satellites"][
            "acronyms"
        ]

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    @patch("s1ifr.produce_list_file_S1.write_safe_to_file_list")
    @patch("s1ifr.produce_list_file_S1.glob.glob")
    def test_list_safe_s1_ifr_fs_success(self, mock_glob, mock_write_file):
        """
        Should find SAFE files and call the writer function when write=True.
        """
        # --- Arrange ---
        # Simulate that glob finds two files on the second day of the date range.
        expected_files = [
            "/archive/datawork/sentinel-1a/L1/IW/S1A_IW_GRDH_1S/2023/122/S1A_IW_GRDH_1SDV_....SAFE",
            "/archive/datawork/sentinel-1a/L1/IW/S1A_IW_GRDH_1S/2023/122/S1A_IW_GRDH_1SDV_....SAFE",
        ]
        # The first call to glob (for the first day) finds nothing, the second finds our files.
        mock_glob.side_effect = [[], expected_files]

        # --- Act ---
        found_files, logpath = produce_list_file_S1.list_safe_s1_ifr_fs(
            startdate="20230501",
            enddate="20230502",
            satellite="S1A",
            level="L1",
            mode="IW",
            formato="GRDH",
            archive_name="datawork",
            write=True,
        )

        # --- Assert ---
        self.assertEqual(found_files, expected_files)
        self.assertEqual(
            mock_glob.call_count, 2
        )  # Called once for each day in the range

        # Check that the glob pattern was constructed correctly for the second day
        expected_pattern = "/archive/datawork/sentinel-1a/L1/IW/S1A_IW_GRDH_1S/2023/122/S1A*.SAFE"
        mock_glob.assert_called_with(expected_pattern)

        # Check that the file writer was called since write=True
        mock_write_file.assert_called_once()

    @patch("s1ifr.produce_list_file_S1.glob.glob")
    def test_find_netcdf_between_2_dates_filters_correctly(self, mock_glob):
        """
        Should return only the netCDF files that are strictly within the date range.
        """
        # --- Arrange ---
        # These are the fake files that glob will "find".
        # Note the timestamps embedded in the filenames.
        fake_files = [
            "/path/to/S1A_IW_GRDH_1S_20230615T100000_.../measurement/s1a-iw-ocn-vv-20230615t100000-.nc",  # Should be included
            "/path/to/S1A_IW_GRDH_1S_20230615T235959_.../measurement/s1a-iw-ocn-vv-20230615t235959-.nc",  # Should be included
            "/path/to/S1A_IW_GRDH_1S_20230616T000000_.../measurement/s1a-iw-ocn-vv-20230616t000000-.nc",  # Should be included
            "/path/to/S1A_IW_GRDH_1S_20230614T235959_.../measurement/s1a-iw-ocn-vv-20230614t235959-.nc",  # Out of bounds (too early)
            "/path/to/S1A_IW_GRDH_1S_20230616T000001_.../measurement/s1a-iw-ocn-vv-20230616t000001-.nc",  # Out of bounds (too late)
        ]
        mock_glob.return_value = fake_files

        start = datetime.datetime(2023, 6, 15, 10, 0, 0)
        stop = datetime.datetime(2023, 6, 16, 0, 0, 0)

        # --- Act ---
        result = produce_list_file_S1.find_netcdf_between_2_dates(
            start, stop, "sentinel-1a", archive_name="datawork"
        )
        # --- Assert ---
        self.assertEqual(len(result), 3)
        self.assertIn(fake_files[0], result)
        self.assertIn(fake_files[1], result)
        self.assertIn(fake_files[2], result)
        self.assertNotIn(fake_files[3], result)
        self.assertNotIn(fake_files[4], result)

    @patch("s1ifr.produce_list_file_S1.getpass.getuser")
    @patch("s1ifr.produce_list_file_S1.open", new_callable=mock_open)
    def test_write_safe_to_file_list(self, mock_file, mock_getuser):
        """
        Should write a list of SAFE paths to the correct file.
        """
        # --- Arrange ---
        mock_getuser.return_value = "testuser"
        safes_to_write = ["/path/to/safe1.SAFE", "/path/to/safe2.SAFE"]
        start_date_str = "20230101"
        end_date_str = "20230102"

        # --- Act ---
        logpath = produce_list_file_S1.write_safe_to_file_list(
            "S1A", start_date_str, end_date_str, safes_to_write
        )

        # --- Assert ---
        expected_logname = f"S1A_{start_date_str}_{end_date_str}_dirSAFE.lst"
        expected_path = (
            f"/home1/scratch/testuser/PRUN_workspace/{expected_logname}"
        )

        self.assertEqual(logpath, expected_path)

        # Check that open was called with the correct path and mode
        mock_file.assert_called_once_with(expected_path, "w")

        # Check that the content was written correctly
        handle = mock_file()
        handle.write.assert_any_call("/path/to/safe1.SAFE\n")
        handle.write.assert_any_call("/path/to/safe2.SAFE\n")
        self.assertEqual(handle.write.call_count, 2)


if __name__ == "__main__":
    unittest.main()
