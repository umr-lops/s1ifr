import pytest
import datetime
import os
from unittest.mock import patch, MagicMock

# Import the functions to test
from s1ifr.match_measu_l1_l2 import getTiffcorresponding2NetCDF, getNCcorresponding2TIFF

# Realistic Sentinel-1 measurement basenames
L2_NC_NAME = "s1a-wv1-ocn-vv-20150911t123908-20150911t123911-007667-00aa41-079.nc"
L1_TIF_NAME = "s1a-wv1-slc-vv-20150911t123908-20150911t123911-007667-00aa41-079.tiff"

@pytest.fixture
def mock_explode_safe():
    """Mocks the ExplodeSAFE class and its return values."""
    with patch("s1ifr.match_measu_l1_l2.ExplodeSAFE") as mock_class:
        instance = mock_class.return_value
        # Default to a date AFTER the IPF 2.43 deployment
        instance.get.return_value = datetime.datetime(2020, 1, 1)
        yield instance

# --- Tests for getTiffcorresponding2NetCDF ---

def test_getTiffcorresponding2NetCDF_modern_exists(mock_explode_safe):
    """Test L2 -> L1 conversion for modern data where path exists directly."""
    l2_path = f"/data/L2_SAFE/measurement/{L2_NC_NAME}"
    l1_safe_dir = "/data/L1_SAFE"
    expected_tiff = f"{l1_safe_dir}/measurement/{L1_TIF_NAME}"

    with patch("s1ifr.match_measu_l1_l2.getL1SAFEcorrespondingToL2SAFE", return_value=l1_safe_dir):
        with patch("os.path.exists", return_value=True):
            res = getTiffcorresponding2NetCDF(l2_path)
            assert res == expected_tiff

def test_getTiffcorresponding2NetCDF_pre_ipf_reindexing(mock_explode_safe):
    """Test L2 -> L1 conversion for old data (pre-2015) where indices are reordered."""
    # Set date to before IPF 2.43
    mock_explode_safe.get.return_value = datetime.datetime(2014, 1, 1)
    
    l2_path = f"/data/L2_SAFE/measurement/{L2_NC_NAME}" # Index 079
    l1_safe_dir = "/data/L1_SAFE"
    
    # Mock the index remapping functions
    with patch("s1ifr.match_measu_l1_l2.getlast_imagette_number_in_safe", return_value=100):
        with patch("s1ifr.match_measu_l1_l2.get_l1_indice", return_value=85): # 079 maps to 085
            with patch("s1ifr.match_measu_l1_l2.getL1SAFEcorrespondingToL2SAFE", return_value=l1_safe_dir):
                # Simulate the direct path not existing, but glob finding the reindexed one
                reindexed_tif = f"{l1_safe_dir}/measurement/s1a-wv1-slc-vv-date-etc-085.tiff"
                
                with patch("os.path.exists", side_effect=[False, True]):
                    with patch("glob.glob", return_value=[reindexed_tif]):
                        res = getTiffcorresponding2NetCDF(l2_path)
                        assert "085.tiff" in res

def test_getTiffcorresponding2NetCDF_not_found(mock_explode_safe):
    """Ensure it returns an empty string if L1 SAFE is not found."""
    # Use a realistic name so .split('-')[8] doesn't crash
    l2_path = f"/data/L2_SAFE/measurement/{L2_NC_NAME}"
    
    with patch("s1ifr.match_measu_l1_l2.getL1SAFEcorrespondingToL2SAFE", return_value=None):
        res = getTiffcorresponding2NetCDF(l2_path)
        assert res == ""

# --- Tests for getNCcorresponding2TIFF ---

def test_getNCcorresponding2TIFF_success(mock_explode_safe):
    """Test L1 -> L2 conversion."""
    l1_path = f"/data/L1_SAFE/measurement/{L1_TIF_NAME}"
    l2_safe_dir = "/data/L2_SAFE"
    expected_nc = f"{l2_safe_dir}/measurement/{L2_NC_NAME}"

    with patch("s1ifr.match_measu_l1_l2.getL1SAFEcorrespondingToL2SAFE", return_value=l2_safe_dir):
        with patch("glob.glob", return_value=[expected_nc]):
            res = getNCcorresponding2TIFF(l1_path)
            assert res == expected_nc

def test_getNCcorresponding2TIFF_glob_fails(mock_explode_safe):
    """Ensure it returns empty string if glob finds nothing."""
    l1_path = f"/data/L1_SAFE/measurement/{L1_TIF_NAME}"
    
    with patch("s1ifr.match_measu_l1_l2.getL1SAFEcorrespondingToL2SAFE", return_value="/data/L2_SAFE"):
        with patch("glob.glob", return_value=[]):
            res = getNCcorresponding2TIFF(l1_path)
            assert res == ""