import datetime
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from s1ifr.clean_sentinel1_duplicates_function import (
    check_duplicate,
    get_ending_processing_time,
    latest_safe_processed,
    spot_dupli_core,
)

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
  acronyms:
    sentinel-1a: "S1A"

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


@pytest.fixture
def config_path():
    """Write a temporary config YAML file and yield its path."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(CONFIG_YAML)
        path = f.name
    yield path
    os.unlink(path)


# --- Tests for get_ending_processing_time ---


def test_get_ending_processing_time_success():
    stop_time_str = "2023-05-10T10:00:00.000000"

    with (
        patch("os.path.isfile", return_value=True),
        patch("os.path.getsize", return_value=100),
        patch("s1ifr.clean_sentinel1_duplicates_function.etree.parse") as mock_parse,
    ):
        mock_tree = MagicMock()
        mock_element = MagicMock()
        mock_element.attrib = {"stop": stop_time_str}
        mock_tree.findall.return_value = [mock_element]
        mock_parse.return_value = mock_tree

        result = get_ending_processing_time("/fake/path.SAFE")

        assert result == datetime.datetime(2023, 5, 10, 10, 0, 0)
        expected_pattern = (
            "./"
            + "/metadataObject/metadataWrap/xmlData/{http://www.esa.int/safe/sentinel-1.0}processing"
        )
        mock_tree.findall.assert_called_once_with(expected_pattern)


def test_get_ending_processing_time_missing_file():
    with patch("os.path.isfile", return_value=False):
        result = get_ending_processing_time("/non/existent.SAFE")
        assert result == datetime.datetime(2014, 1, 1)


# --- Tests for latest_safe_processed ---


def test_latest_safe_processed():
    dupes = ["path1", "path2", "path3"]
    dates = [
        datetime.datetime(2020, 1, 1),
        datetime.datetime(2023, 1, 1),
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


def test_check_duplicate_dryrun(config_path):
    safe_path = "/archive/my_file.SAFE"
    mock_results = (0, ["latest_ver", "old_ver"], [10, 5])

    with patch(
        "s1ifr.clean_sentinel1_duplicates_function.spot_dupli_core",
        return_value=mock_results,
    ):
        with patch(
            "s1ifr.clean_sentinel1_duplicates_function.quarantine_ticket"
        ) as mock_quarantine:
            deleted_count = check_duplicate(
                safe_path, dryrun=True, config_path=config_path
            )

            assert deleted_count == 1
            mock_quarantine.assert_not_called()


def test_check_duplicate_execution(config_path):
    """Test that quarantine_ticket is called on the older duplicate when dryrun=False."""
    safe_path = "/archive/my_file.SAFE"
    # index 1 is latest, so "old_ver" at index 0 should be quarantined
    mock_results = (1, ["old_ver", "latest_ver"], [5, 10])

    with patch(
        "s1ifr.clean_sentinel1_duplicates_function.spot_dupli_core",
        return_value=mock_results,
    ):
        with patch(
            "s1ifr.clean_sentinel1_duplicates_function.quarantine_ticket"
        ) as mock_quarantine:
            deleted_count = check_duplicate(
                safe_path, dryrun=False, config_path=config_path
            )

            assert deleted_count == 1
            mock_quarantine.assert_called_once_with(
                "old_ver", "datawork", config_path=config_path
            )
