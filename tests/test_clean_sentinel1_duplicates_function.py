import datetime
from unittest.mock import MagicMock, patch

# Import the functions
from s1ifr.clean_sentinel1_duplicates_function import (
    check_duplicate,
    get_ending_processing_time,
    latest_safe_processed,
    spot_dupli_core,
)

# --- Tests for get_ending_processing_time ---


def test_get_ending_processing_time_success():
    """Test extracting the stop time by mocking the XML tree structure."""
    stop_time_str = "2023-05-10T10:00:00.000000"

    # We patch etree.parse where it is USED in the script
    with (
        patch("os.path.isfile", return_value=True),
        patch("os.path.getsize", return_value=100),
        patch(
            "s1ifr.clean_sentinel1_duplicates_function.etree.parse"
        ) as mock_parse,
    ):

        # 1. Create a chain of mocks to represent tree -> element -> attrib
        mock_tree = MagicMock()
        mock_element = MagicMock()

        # 2. Set the attrib['stop'] to a REAL string to satisfy strptime
        mock_element.attrib = {"stop": stop_time_str}

        # 3. tree.findall() should return a list containing our mock_element
        mock_tree.findall.return_value = [mock_element]

        # 4. etree.parse() returns our mock_tree
        mock_parse.return_value = mock_tree

        result = get_ending_processing_time("/fake/path.SAFE")

        # Verify the parsing worked
        assert result == datetime.datetime(2023, 5, 10, 10, 0, 0)
        # Verify the correct pattern was used in findall
        expected_pattern = (
            "./"
            + "/metadataObject/metadataWrap/xmlData/{http://www.esa.int/safe/sentinel-1.0}processing"
        )
        mock_tree.findall.assert_called_once_with(expected_pattern)


def test_get_ending_processing_time_missing_file():
    """Test that a dummy date is returned if the manifest is missing."""
    with patch("os.path.isfile", return_value=False):
        result = get_ending_processing_time("/non/existent.SAFE")
        assert result == datetime.datetime(2014, 1, 1)


# --- Tests for latest_safe_processed ---


def test_latest_safe_processed():
    """Verify that the newest date index is correctly identified."""
    dupes = ["path1", "path2", "path3"]
    dates = [
        datetime.datetime(2020, 1, 1),
        datetime.datetime(2023, 1, 1),  # Latest
        datetime.datetime(2022, 1, 1),
    ]

    with patch(
        "s1ifr.clean_sentinel1_duplicates_function.get_ending_processing_time",
        side_effect=dates,
    ):
        idx, paths, stoptimes = latest_safe_processed(dupes)
        assert idx == 1
        assert paths == dupes
        assert stoptimes[1] == datetime.datetime(2023, 1, 1)


# --- Tests for spot_dupli_core ---


def test_spot_dupli_core():
    """Test finding duplicates via os.walk matching."""
    safe_base = "S1A_IW_SLC__1SDV_20230101.SAFE"
    mock_walk = [
        (
            "/archive",
            [
                "S1A_IW_SLC__1SDV_20230101_V1.SAFE",
                "S1A_IW_SLC__1SDV_20230101_V2.SAFE",
            ],
            [],
        )
    ]

    with patch("os.walk", return_value=mock_walk):
        with patch(
            "s1ifr.clean_sentinel1_duplicates_function.latest_safe_processed",
            return_value=(0, ["p1", "p2"], [None, None]),
        ):
            idx, occs, stops = spot_dupli_core(safe_base, "/archive")
            assert len(occs) == 2


# --- Tests for check_duplicate ---


def test_check_duplicate_dryrun():
    """Test check_duplicate returns count but doesn't call quarantine on dryrun."""
    safe_path = "/archive/my_file.SAFE"
    # index 0 is latest, index 1 is old
    mock_results = (0, ["latest_ver", "old_ver"], [10, 5])

    with patch(
        "s1ifr.clean_sentinel1_duplicates_function.spot_dupli_core",
        return_value=mock_results,
    ):
        # FIX: Patch the function where it is USED (in your script), not where it is defined
        with patch(
            "s1ifr.clean_sentinel1_duplicates_function.quarantine_ticket"
        ) as mock_quarantine:
            deleted_count = check_duplicate(safe_path, dryrun=True)

            assert deleted_count == 1
            mock_quarantine.assert_not_called()


def test_check_duplicate_execution():
    """Test that quarantine_ticket is called when dryrun is False."""
    safe_path = "/archive/my_file.SAFE"
    # index 1 is the latest, so index 0 ("old_ver") should be deleted
    mock_results = (1, ["old_ver", "latest_ver"], [5, 10])

    with patch(
        "s1ifr.clean_sentinel1_duplicates_function.spot_dupli_core",
        return_value=mock_results,
    ):
        # FIX: Patch the function where it is USED
        with patch(
            "s1ifr.clean_sentinel1_duplicates_function.quarantine_ticket"
        ) as mock_quarantine:
            deleted_count = check_duplicate(safe_path, dryrun=False)

            assert deleted_count == 1
            # Now the mock will correctly capture the call
            mock_quarantine.assert_called_once_with("old_ver", "datawork")
