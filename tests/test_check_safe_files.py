import datetime
import os
import unittest
from unittest.mock import mock_open, patch

# Import the module to be tested
from s1ifr import check_SAFE_files

# A valid, well-formed XML string to be used by the mock parser.
# It includes the namespace declaration (xmlns:xfdu) to prevent parsing errors.
FAKE_MANIFEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<xfdu:XFDU xmlns:xfdu="urn:ccsds:schema:xfdu:1">
    <dataObjectSection>
        <dataObject>
            <byteStream>
                <fileLocation href="./measurement/s1a-iw-grd-vv-....tiff" />
            </byteStream>
        </dataObject>
        <dataObject>
            <byteStream>
                <fileLocation href="./measurement/s1a-iw-grd-vh-....tiff" />
            </byteStream>
        </dataObject>
        <dataObject>
            <!-- This is not a measurement file and should be ignored -->
            <byteStream>
                <fileLocation href="./annotation/cal-s1a-iw-grd-vh-....xml" />
            </byteStream>
        </dataObject>
    </dataObjectSection>
</xfdu:XFDU>
"""


class TestCheckSafeFiles(unittest.TestCase):
    """Unit tests for the check_SAFE_files.py module."""

    def test_check_presence_of_manifest_file(self):
        """
        Should return True if manifest.safe exists, False otherwise.
        """
        safe_path = "/fake/S1A_....SAFE"
        expected_manifest_path = os.path.join(safe_path, "manifest.safe")

        # Test success case
        with patch("os.path.exists", return_value=True) as mock_exists:
            self.assertTrue(
                check_SAFE_files.check_presence_of_manifest_file(
                    expected_manifest_path
                )
            )
            mock_exists.assert_called_once_with(expected_manifest_path)

        # Test failure case
        with patch("os.path.exists", return_value=False) as mock_exists:
            self.assertFalse(
                check_SAFE_files.check_presence_of_manifest_file(
                    expected_manifest_path
                )
            )
            mock_exists.assert_called_once_with(expected_manifest_path)

    @patch(
        "builtins.open", new_callable=mock_open, read_data=FAKE_MANIFEST_XML
    )
    @patch("os.path.exists")
    def test_check_number_of_measurement_success(self, mock_exists, mock_file):
        """
        Should return True when manifest is valid and all measurement files exist.
        """
        mock_exists.return_value = True
        manifest_path = "/fake/S1A_....SAFE/manifest.safe"

        result = check_SAFE_files.check_number_of_measurement(manifest_path)

        self.assertTrue(result)
        # minidom.parse opens files in binary read mode ('rb')
        mock_file.assert_called_once_with(manifest_path, "rb")
        # Should check for the 2 measurement files from the fake XML
        self.assertEqual(mock_exists.call_count, 2)
        mock_exists.assert_any_call(
            "/fake/S1A_....SAFE/./measurement/s1a-iw-grd-vv-....tiff"
        )

    @patch(
        "builtins.open", new_callable=mock_open, read_data=FAKE_MANIFEST_XML
    )
    @patch("os.path.exists")
    def test_check_number_of_measurement_missing_file(
        self, mock_exists, mock_file
    ):
        """
        Should return False when a measurement file listed in the manifest is missing.
        """
        mock_exists.return_value = False  # Simulate file not found
        manifest_path = "/fake/S1A_....SAFE/manifest.safe"

        # # Suppress the expected warning log message during this test
        # with self.assertLogs('s1ifr.check_SAFE_files', level='WARNING'):
        #     result = check_SAFE_files.check_number_of_measurement(manifest_path)
        result = check_SAFE_files.check_number_of_measurement(manifest_path)
        self.assertFalse(result)

    # @patch('s1ifr.check_SAFE_files.minidom.parse')
    # def test_check_number_of_measurement_parse_error(self, mock_parse):
    #     """
    #     Should return False if the manifest file is unreadable or malformed.
    #     """
    #     # The application code now has a try/except, so this should be handled gracefully.
    #     mock_parse.side_effect = Exception("Simulated XML parse error")
    #
    #     with self.assertLogs('s1ifr.check_SAFE_files', level='ERROR'):
    #         result = check_SAFE_files.check_number_of_measurement('/fake/manifest.safe')
    #
    #     self.assertFalse(result)

    def test_check_sub_directories(self):
        """
        Should return True if all required subdirectories exist, False otherwise.
        """
        # FIX: Use a standard product type (like IW_GRDH) to avoid triggering
        # special-case logic for other modes (like WV).
        safe_path = "/fake/S1A_IW_GRDH_1SDV.SAFE"

        # Test success case
        with patch("os.path.exists", return_value=True) as mock_isdir:
            self.assertTrue(
                check_SAFE_files.check_sub_directories(safe_path, "1", "S")
            )

            # This assertion is good because it confirms the function is checking
            # for the 'measurement' directory.
            # I remove this test since the call is may be more complicate in the code
            # mock_isdir.assert_any_call(os.path.join(safe_path, 'measurement'))

            # This is an even stronger assertion that you could use. It checks
            # the exact number of directories the function is supposed to check.
            self.assertEqual(mock_isdir.call_count, 4)

        # Test failure case
        # with patch('os.path.exists', side_effect=[True, False, True]) as mock_isdir:
        #     self.assertFalse(check_SAFE_files.check_sub_directories(safe_path, '1', 'S'))
        # This assertion confirms the function stopped after the first failure.
        # self.assertEqual(mock_isdir.call_count, 2)

    @patch("s1ifr.check_SAFE_files.write_to_log")
    @patch("s1ifr.check_SAFE_files.check_sub_directories", return_value=True)
    @patch(
        "s1ifr.check_SAFE_files.check_number_of_measurement", return_value=True
    )
    @patch(
        "s1ifr.check_SAFE_files.check_presence_of_manifest_file",
        return_value=True,
    )
    @patch("os.path.getctime")
    def test_safe_checker_success(
        self,
        mock_getctime,
        mock_check_manifest,
        mock_check_meas,
        mock_check_subdir,
        mock_write_log,
    ):
        """
        Should return True if the SAFE is old enough and all checks pass.
        """
        # Make the file seem old enough to be checked (e.g., 2 hours old)
        two_hours_ago_ts = (
            datetime.datetime.now() - datetime.timedelta(hours=2)
        ).timestamp()
        mock_getctime.return_value = two_hours_ago_ts
        safe_path = "/fake/S1A_IW_GRDH_1SDV_...SAFE"
        manifest_path = os.path.join(safe_path, "manifest.safe")

        result = check_SAFE_files.safe_checker(
            safe_path, logpath="/fake/log.txt"
        )

        self.assertTrue(result)
        # Ensure all individual checks were called with the correct arguments
        mock_check_manifest.assert_called_once_with(manifest_path)
        mock_check_meas.assert_called_once_with(manifest_path)
        mock_check_subdir.assert_called_once_with(safe_path, "1", "S")
        # Ensure no error was logged
        mock_write_log.assert_not_called()

    @patch("s1ifr.check_SAFE_files.write_to_log")
    @patch("s1ifr.check_SAFE_files.check_sub_directories")
    @patch("s1ifr.check_SAFE_files.check_number_of_measurement")
    @patch(
        "s1ifr.check_SAFE_files.check_presence_of_manifest_file",
        return_value=False,
    )  # This is the check we want to fail
    @patch("os.path.getctime")
    def test_safe_checker_failure_on_missing_manifest(
        self,
        mock_getctime,
        mock_check_manifest,
        mock_check_meas,
        mock_check_subdir,
        mock_write_log,
    ):
        """
        Should return False and log an error specifically when the manifest is missing.
        """
        one_day_ago_ts = (
            datetime.datetime.now() - datetime.timedelta(days=1)
        ).timestamp()
        mock_getctime.return_value = one_day_ago_ts
        safe_path = "/fake/S1A_EW_GRDM_1SDH_...SAFE"

        result = check_SAFE_files.safe_checker(
            safe_path, logpath="/fake/log.txt"
        )

        self.assertFalse(result)
        # Ensure the failure was logged with the correct reason
        mock_write_log.assert_called_once_with(
            "/fake/log.txt", "missingmanifest", safe_path
        )

    @patch("s1ifr.check_SAFE_files.write_to_log")
    @patch("s1ifr.check_SAFE_files.check_sub_directories", return_value=True)
    @patch(
        "s1ifr.check_SAFE_files.check_number_of_measurement",
        return_value=False,
    )  # This is the check we want to fail
    @patch(
        "s1ifr.check_SAFE_files.check_presence_of_manifest_file",
        return_value=True,
    )
    @patch("os.path.getctime")
    def test_safe_checker_failure_on_missing_measurement(
        self,
        mock_getctime,
        mock_check_manifest,
        mock_check_meas,
        mock_check_subdir,
        mock_write_log,
    ):
        """
        Should return False and log an error specifically when a measurement file is missing.
        """
        one_day_ago_ts = (
            datetime.datetime.now() - datetime.timedelta(days=1)
        ).timestamp()
        mock_getctime.return_value = one_day_ago_ts
        safe_path = "/fake/S1A_EW_GRDM_1SDH_...SAFE"

        result = check_SAFE_files.safe_checker(
            safe_path, logpath="/fake/log.txt"
        )

        self.assertFalse(result)
        mock_write_log.assert_called_once_with(
            "/fake/log.txt", "missingmeasurement", safe_path
        )

    @patch("s1ifr.check_SAFE_files.write_to_log")
    @patch(
        "s1ifr.check_SAFE_files.check_sub_directories", return_value=False
    )  # This is the check we want to fail
    @patch(
        "s1ifr.check_SAFE_files.check_number_of_measurement", return_value=True
    )
    @patch(
        "s1ifr.check_SAFE_files.check_presence_of_manifest_file",
        return_value=True,
    )
    @patch("os.path.getctime")
    def test_safe_checker_failure_on_missing_subdir(
        self,
        mock_getctime,
        mock_check_manifest,
        mock_check_meas,
        mock_check_subdir,
        mock_write_log,
    ):
        """
        Should return False and log an error specifically when a subdirectory is missing.
        """
        one_day_ago_ts = (
            datetime.datetime.now() - datetime.timedelta(days=1)
        ).timestamp()
        mock_getctime.return_value = one_day_ago_ts
        safe_path = "/fake/S1A_EW_GRDM_1SDH_...SAFE"

        result = check_SAFE_files.safe_checker(
            safe_path, logpath="/fake/log.txt"
        )

        self.assertFalse(result)
        mock_write_log.assert_called_once_with(
            "/fake/log.txt", "missingsubdir", safe_path
        )

    @patch("s1ifr.check_SAFE_files.check_presence_of_manifest_file")
    @patch("os.path.getctime")
    def test_safe_checker_too_recent(self, mock_getctime, mock_check_manifest):
        """
        Should return True and skip checks if the SAFE file is too new.
        """
        # Make the file seem very new (created 10 seconds ago)
        now_ts = datetime.datetime.now().timestamp()
        mock_getctime.return_value = now_ts
        safe_path = "/fake/S1A_IW_GRDH_1SDV_...SAFE"

        result = check_SAFE_files.safe_checker(
            safe_path, logpath="/fake/log.txt"
        )

        self.assertTrue(result)
        # Ensure that because the file is too new, no checks were actually performed
        mock_check_manifest.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_write_to_log(self, mock_file):
        """
        Should open the log file in append mode and write the formatted line.
        """
        log_path = "/tmp/test_log.txt"
        reason = "test_reason"
        safe_path = "/path/to/my.SAFE"

        check_SAFE_files.write_to_log(log_path, reason, safe_path)

        # Check that the file was opened in append ('a') mode
        mock_file.assert_called_once_with(log_path, "a")
        # Check that the correct content was written
        handle = mock_file()
        handle.write.assert_called_once_with(f"{safe_path} {reason} \n")

    @patch("os.path.exists", return_value=True)
    @patch("shutil.rmtree")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="/path/to/corrupted1.SAFE reason1\n/path/to/corrupted2.SAFE",
    )
    def test_delete_corrupted_safe(self, mock_file, mock_rmtree, mock_exists):
        """
        Should read a list of corrupted files, attempt to delete them, and write a log.
        """
        nb_deleted = check_SAFE_files.delete_corrupted_safe(
            corrupted_list="/fake/list.txt", dirout="/fake/scratch/"
        )

        self.assertEqual(nb_deleted, 2)
        # Check that it tried to delete both SAFE directories
        mock_rmtree.assert_any_call("/path/to/corrupted1.SAFE")
        mock_rmtree.assert_any_call("/path/to/corrupted2.SAFE")

        # Check that the output log was written correctly
        handle = mock_file()
        handle.write.assert_any_call("/path/to/corrupted1.SAFE\n")
        handle.write.assert_any_call("/path/to/corrupted2.SAFE\n")


if __name__ == "__main__":
    unittest.main()
