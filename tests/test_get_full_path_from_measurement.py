import pytest
import datetime
import os
from unittest.mock import patch, MagicMock

# Import the functions to test
from s1ifr.get_full_path_from_measurement import (
    get_full_path_from_measu,
    get_full_path_ocn_wv_from_approximate_date,
    get_full_path_with_safe_and_measu
)

@pytest.fixture
def mock_conf():
    """Provides a dummy configuration."""
    return {
        "paths": {
            "datawork": {
                "archive_esa": "/archive/esa",
            },
            "scale": {
                "archive_esa": "/scale/esa",
            }
        }
    }

# --- Tests for get_full_path_from_measu ---

def test_get_full_path_from_measu_found_first_try(mock_conf):
    """Test path resolution when the file is found on the first glob attempt."""
    measurement = "s1a-wv1-ocn-vv-20150911t123908-20150911t123911-007667-00aa41-079.nc"
    expected_path = "/archive/esa/sentinel-1a/L2/WV/S1A_WV_OCN__2S/2015/254/SOME_SAFE/measurement/" + measurement
    
    with patch("s1ifr.get_full_path_from_measurement.load_config", return_value=mock_conf):
        with patch("glob.glob", return_value=[expected_path]):
            res = get_full_path_from_measu(measurement)
            assert res == expected_path

def test_get_full_path_from_measu_found_day_before(mock_conf):
    """Test the fallback logic: not found today, but found in the previous day folder."""
    measurement = "s1a-wv1-ocn-vv-20150911t123908-20150911t123911-007667-00aa41-079.nc"
    day_before_path = "/archive/esa/sentinel-1a/L2/WV/S1A_WV_OCN__2S/2015/253/SOME_SAFE/measurement/" + measurement
    
    with patch("s1ifr.get_full_path_from_measurement.load_config", return_value=mock_conf):
        # First call to glob (today) returns empty, second call (yesterday) returns a path
        with patch("glob.glob", side_effect=[[], [day_before_path]]):
            res = get_full_path_from_measu(measurement)
            assert res == day_before_path

def test_get_full_path_from_measu_not_found(mock_conf):
    """Test when glob returns nothing for both attempts."""
    measurement = "s1a-wv1-ocn-vv-20150911t123908-20150911t123911-007667-00aa41-079.nc"
    
    with patch("s1ifr.get_full_path_from_measurement.load_config", return_value=mock_conf):
        with patch("glob.glob", return_value=[]):
            res = get_full_path_from_measu(measurement)
            assert res is None

# --- Tests for get_full_path_ocn_wv_from_approximate_date ---

def test_get_full_path_ocn_wv_approximate_found(mock_conf):
    """Test searching for OCN WV by date with a 1-second shift."""
    datedt = datetime.datetime(2023, 1, 1, 12, 0, 0)
    sat = "S1A"
    expected_file = "/archive/esa/sentinel-1a/L2/WV/S1A_WV_OCN__2S/2023/001/SAFE/measurement/file.nc"
    
    with patch("s1ifr.get_full_path_from_measurement.load_config", return_value=mock_conf):
        # Simulate: -3s, -2s, -1s, 0s = empty. +1s = found.
        # nb_seconds_delta = 3 implies a loop of 7 iterations (-3 to +3)
        with patch("glob.glob", side_effect=[[], [], [], [], [expected_file]]):
            res = get_full_path_ocn_wv_from_approximate_date(datedt, sat, nb_seconds_delta=3)
            assert res == expected_file

# --- Tests for get_full_path_with_safe_and_measu ---

def test_get_full_path_with_safe_and_measu_logic(mock_conf):
    """Verify string construction for specific SAFE and measurement pair."""
    safebase = "S1A_WV_OCN__2SSV_20230101.SAFE"
    measu_base = "s1a-wv1-ocn-vv-20230101t120000-20230101t120003-012345-0AB123-001.nc"
    
    with patch("s1ifr.get_full_path_from_measurement.load_config", return_value=mock_conf):
        res = get_full_path_with_safe_and_measu(safebase, measu_base)
        
        # Check components of the path
        assert "sentinel-1a" in res
        assert "L2" in res
        assert "2023" in res
        assert "001" in res # Day of year for Jan 1st
        assert res.endswith(measu_base)
        assert safebase in res

def test_get_full_path_with_safe_and_measu_slc(mock_conf):
    """Check L1 / SLC logic in path construction."""
    safebase = "S1A_WV_SLC__1SSV_20230101.SAFE"
    measu_base = "s1a-wv1-slc-vv-20230101t120000-20230101t120003-012345-0AB123-001.tiff"
    
    with patch("s1ifr.get_full_path_from_measurement.load_config", return_value=mock_conf):
        res = get_full_path_with_safe_and_measu(safebase, measu_base)
        
        assert "L1" in res
        assert "S1A_WV_SLC__1S" in res
        assert res.endswith(".tiff")