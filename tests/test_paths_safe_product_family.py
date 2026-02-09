import pytest
import pandas as pd
import datetime
import os
from collections import defaultdict
from unittest.mock import patch, MagicMock

# Import your functions
from s1ifr.paths_safe_product_family import (
    _resolve_slc_path, 
    add_L1B, 
    add_L1C, 
    add_L2WAV
)

# A valid-looking Sentinel-1 SAFE filename for splitting logic to work
VALID_SAFE_NAME = "S1A_IW_SLC__1SDV_20230101T120000_20230101T120025_012345_0AB123_4567.SAFE"

@pytest.fixture
def mock_config():
    """Provides a dummy configuration dictionary."""
    return {
        "paths": {
            "datawork": {
                "dir_outs_l1b": ["/archive/l1b_out"],
                "dir_outs_l1c": ["/archive/l1c_out"],
                "dir_out_l2wav": ["/archive/l2wav_out"]
            }
        },
        "DEFAULT_VERSIONS_L1B": ["A14"],
        "DEFAULT_VERSIONS_L1C": ["B17"],
        "DEFAULT_VERSIONS_L2WAV": ["V01"]
    }

@pytest.fixture
def sample_df():
    """Simple dataframe with one SLC identifier."""
    return pd.DataFrame({"L1_SLC": [VALID_SAFE_NAME]})

# --- Tests for _resolve_slc_path ---

def test_resolve_slc_path_absolute(mocker):
    """Test when an absolute path is provided and exists."""
    mocker.patch("os.path.exists", return_value=True)
    path = f"/absolute/path/to/{VALID_SAFE_NAME}"
    assert _resolve_slc_path(path) == path

def test_resolve_slc_path_archive_hit(mocker):
    """Test when a filename is provided and found in 'datawork' archive."""
    mocker.patch("os.path.exists", side_effect=lambda x: "datawork" in str(x))
    mocker.patch("s1ifr.get_path_from_base_safe.get_path_from_base_safe", 
                 side_effect=lambda name, archive_name: f"/{archive_name}/{name}")
    
    result = _resolve_slc_path(VALID_SAFE_NAME)
    assert result == f"/datawork/{VALID_SAFE_NAME}"

# --- Tests for add_L1B ---

@patch("s1ifr.paths_safe_product_family.load_config")
def test_add_L1B_success(mock_load_conf, mock_config, sample_df, mocker):
    """Test successful L1B path discovery."""
    mock_load_conf.return_value = mock_config
    
    # FIX: Return a path containing a valid SAFE name
    mocker.patch("s1ifr.paths_safe_product_family._resolve_slc_path", 
                 return_value=f"/archive/datawork/{VALID_SAFE_NAME}")
    
    # Mock file existence: True only for the expected L1B output path
    def side_effect(path):
        return "l1b_out" in str(path) and "A14" in str(path)
    
    mocker.patch("os.path.exists", side_effect=side_effect)
    
    df_out, cpt = add_L1B(sample_df.copy())
    
    assert "L1B_XSP_A14" in df_out.columns
    assert df_out["L1B_XSP_A14"].iloc[0] != ""
    assert cpt["L1B_A14_found"] == 1
    assert cpt["L1B_found"] == 1

# --- Tests for add_L1C ---

@patch("s1ifr.paths_safe_product_family.load_config")
def test_add_L1C_absent(mock_load_conf, mock_config, sample_df, mocker):
    """Test L1C logic when files do not exist."""
    mock_load_conf.return_value = mock_config
    
    # FIX: Return a path containing a valid SAFE name
    mocker.patch("s1ifr.paths_safe_product_family._resolve_slc_path", 
                 return_value=f"/archive/datawork/{VALID_SAFE_NAME}")
    mocker.patch("os.path.exists", return_value=False)
    
    df_out, cpt = add_L1C(sample_df.copy())
    
    assert df_out["L1C_XSP_B17"].iloc[0] == ""
    assert cpt["L1C_B17_absent"] == 1
    assert cpt["L1C_absent"] == 1

# --- Tests for add_L2WAV ---

@patch("s1ifr.paths_safe_product_family.load_config")
def test_add_L2WAV_path_logic(mock_load_conf, mock_config, sample_df, mocker):
    """Verify that L2WAV correctly renames SLC to WAV and 1S to 2S."""
    mock_load_conf.return_value = mock_config
    
    # FIX: Ensure filename has 1SDV for the rename test
    slc_path = f"/archive/{VALID_SAFE_NAME}"
    mocker.patch("s1ifr.paths_safe_product_family._resolve_slc_path", return_value=slc_path)
    
    mocker.patch("os.path.exists", return_value=True)
    
    df_out, cpt = add_L2WAV(sample_df.copy(), versions=["V01"])
    
    found_path = df_out["L2_WAV_V01"].iloc[0]
    assert "WAV" in found_path
    assert "_2S" in found_path
    assert "V01" in found_path
    assert cpt["L2_WAV_V01_found"] == 1

def test_add_L2WAV_no_slc(sample_df, mocker):
    """Test L2WAV behavior when the underlying SLC cannot be resolved."""
    mock_conf_data = {
        "paths": {"datawork": {"dir_out_l2wav": ["/out"]}},
        "DEFAULT_VERSIONS_L2WAV": ["V1"]
    }
    with patch("s1ifr.paths_safe_product_family.load_config", return_value=mock_conf_data):
        mocker.patch("s1ifr.paths_safe_product_family._resolve_slc_path", return_value=None)
        
        df_out, cpt = add_L2WAV(sample_df.copy())
        
        assert cpt["L2WAV_absent"] == 1
        assert df_out["L2_WAV_V1"].iloc[0] == ""