import unittest
from unittest.mock import patch, MagicMock
import datetime
from s1ifr.match_SLC_GRD import match_SLC_GRD


class TestMatchSlcGr(unittest.TestCase):
    """Unit tests for the match_SLC_GRD function."""

    @patch('s1ifr.match_SLC_GRD.glob.glob')
    @patch('s1ifr.match_SLC_GRD.get_path_from_base_safe')
    @patch('s1ifr.match_SLC_GRD.ExplodeSAFE')
    def test_finds_grd_from_slc_on_datawork(self, mock_explode_safe, mock_get_path, mock_glob):
        """
        Should find a matching GRDH file for an SLC input on the first archive ('datawork').
        """
        # --- Arrange ---
        slc_name = 'S1A_IW_SLC__1SDV_20220901T055632_20220901T055659_044814_055A8B_939A.SAFE'

        # This is the file we expect glob to find
        expected_grd_name = 'S1A_IW_GRDH_1SDV_20220901T055633_20220901T055700_044814_055A8B_1234.SAFE'
        expected_grd_path = f'/datawork/some/path/{expected_grd_name}'

        # Configure the mock for ExplodeSAFE to handle different inputs
        def explode_side_effect(filename):
            mock_instance = MagicMock()
            if 'SLC' in filename or 'GRDH' in slc_name.replace('SLC_', 'GRDH'):
                # This is the input file being parsed
                mock_instance.get.return_value = datetime.datetime(2022, 9, 1, 5, 56, 32)
            elif expected_grd_name in filename:
                # This is the file "found" by glob
                mock_instance.get.return_value = datetime.datetime(2022, 9, 1, 5, 56, 33)  # 1 sec diff
            return mock_instance

        mock_explode_safe.side_effect = explode_side_effect

        # Configure the mock for get_path_from_base_safe
        mock_get_path.return_value = '/datawork/some/path/S1A_IW_GRDH_...SAFE'

        # Configure the mock for glob.glob to "find" our expected file
        mock_glob.return_value = [expected_grd_path]

        # --- Act ---
        result = match_SLC_GRD(slc_name)

        # --- Assert ---
        self.assertEqual(result, expected_grd_path)
        mock_get_path.assert_called_once_with(slc_name.replace('SLC_', 'GRDH'), archive_name='datawork')
        mock_glob.assert_called_once()

    @patch('s1ifr.match_SLC_GRD.glob.glob')
    @patch('s1ifr.match_SLC_GRD.get_path_from_base_safe')
    @patch('s1ifr.match_SLC_GRD.ExplodeSAFE')
    def test_finds_slc_from_grd_on_scale(self, mock_explode_safe, mock_get_path, mock_glob):
        """
        Should find a matching SLC file for a GRDH input, falling back to the 'scale' archive.
        """
        # --- Arrange ---
        grd_name = 'S1A_IW_GRDH_1SDV_20220901T055633_20220901T055700_044814_055A8B_1234.SAFE'
        expected_slc_name = 'S1A_IW_SLC__1SDV_20220901T055632_20220901T055659_044814_055A8B_939A.SAFE'
        expected_slc_path = f'/scale/some/path/{expected_slc_name}'

        # Configure ExplodeSAFE mock
        def explode_side_effect(filename):
            mock_instance = MagicMock()
            if 'GRDH' in filename or 'SLC' in grd_name.replace('GRDH', 'SLC_'):
                mock_instance.get.return_value = datetime.datetime(2022, 9, 1, 5, 56, 33)
            elif expected_slc_name in filename:
                mock_instance.get.return_value = datetime.datetime(2022, 9, 1, 5, 56, 32)  # 1 sec diff
            return mock_instance

        mock_explode_safe.side_effect = explode_side_effect

        # Simulate finding nothing on 'datawork', but finding the file on 'scale'
        mock_get_path.side_effect = [
            '/datawork/dummy/path.SAFE',  # First call
            '/scale/some/path/S1A_IW_SLC_...SAFE'  # Second call
        ]
        mock_glob.side_effect = [
            [],  # First call (for datawork) returns no files
            [expected_slc_path]  # Second call (for scale) finds the file
        ]

        # --- Act ---
        result = match_SLC_GRD(grd_name, type_input='GRDH', type_seek='SLC_')

        # --- Assert ---
        self.assertEqual(result, expected_slc_path)
        self.assertEqual(mock_get_path.call_count, 2)  # Called for both archives
        self.assertEqual(mock_glob.call_count, 2)

    @patch('s1ifr.match_SLC_GRD.glob.glob')
    @patch('s1ifr.match_SLC_GRD.get_path_from_base_safe')
    @patch('s1ifr.match_SLC_GRD.ExplodeSAFE')
    def test_returns_none_if_no_match_found(self, mock_explode_safe, mock_get_path, mock_glob):
        """
        Should return None if no matching file is found in any archive.
        """
        # --- Arrange ---
        slc_name = 'S1A_IW_SLC__1SDV_20220901T055632_20220901T055659_044814_055A8B_939A.SAFE'
        mock_explode_safe.return_value.get.return_value = datetime.datetime.now()
        mock_get_path.return_value = '/dummy/path.SAFE'

        # Simulate glob finding nothing on both archives
        mock_glob.return_value = []

        # --- Act ---
        result = match_SLC_GRD(slc_name)

        # --- Assert ---
        self.assertIsNone(result)
        self.assertEqual(mock_get_path.call_count, 2)  # Should check both archives
        self.assertEqual(mock_glob.call_count, 2)

    @patch('s1ifr.match_SLC_GRD.glob.glob')
    @patch('s1ifr.match_SLC_GRD.get_path_from_base_safe')
    @patch('s1ifr.match_SLC_GRD.ExplodeSAFE')
    def test_returns_none_if_time_diff_too_large(self, mock_explode_safe, mock_get_path, mock_glob):
        """
        Should return None if the only potential match has a start time outside the threshold.
        """
        # --- Arrange ---
        slc_name = 'S1A_IW_SLC__1SDV_20220901T055632_20220901T055659_044814_055A8B_939A.SAFE'
        # This file has a 5-second time difference, which is > the default 3-second threshold
        found_grd_name = 'S1A_IW_GRDH_1SDV_20220901T055637_20220901T055704_044814_055A8B_ABCD.SAFE'
        found_grd_path = f'/datawork/some/path/{found_grd_name}'

        def explode_side_effect(filename):
            mock_instance = MagicMock()
            if 'SLC' in filename:
                mock_instance.get.return_value = datetime.datetime(2022, 9, 1, 5, 56, 32)
            elif found_grd_name in filename:
                mock_instance.get.return_value = datetime.datetime(2022, 9, 1, 5, 56, 37)  # 5 sec diff
            return mock_instance

        mock_explode_safe.side_effect = explode_side_effect

        mock_get_path.return_value = '/dummy/path.SAFE'
        mock_glob.return_value = [found_grd_path]

        # --- Act ---
        result = match_SLC_GRD(slc_name)

        # --- Assert ---
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()