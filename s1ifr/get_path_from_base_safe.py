"""
Functions to resolve full paths for Sentinel-1 SAFE products in the Ifremer archive.

author: Antoine Grouazel
"""

import glob
import logging
import os

from s1ifr.explodesafename import (
    ExplodeSAFE,
    check_safe_name_match_expected_s1_pattern,
)
from s1ifr.SAFEsortingfunctions import which_archive_dir


def get_safe_basename_from_fullpath_measu(fullpathmeasu: str) -> str:
    """Extracts the SAFE product's basename from a full path to a measurement file.

    For example, given '/path/to/S1A...SAFE/measurement/s1a-iw-grd-vv-....tiff',
    it returns 'S1A...SAFE'.

    Args:
        fullpathmeasu: The full path to a measurement file inside a SAFE directory.

    Returns:
        The basename of the parent .SAFE directory.
    """
    # os.path.dirname() is a clearer way to go up the directory tree.
    safe_path = os.path.dirname(os.path.dirname(fullpathmeasu))
    return os.path.basename(safe_path)


def get_path_from_base_safe(
    safe_basename: str,
    archive_name: str = "datawork",
    check_existence: bool = False,
) -> str | None:
    """Constructs the full, absolute path for a given SAFE product basename.

    This function resolves the path within the specified Ifremer archive structure.
    If the basename contains a wildcard ('*'), it attempts to find the first
    matching file.

    Args:
        safe_basename: The name of the SAFE product.
            (e.g., "S1A_IW_OCN__2SDV_20150731T222653_20150731T222719_007061_0099AE_B180.SAFE")
        archive_name: The target archive, either 'datawork' or 'scale'.
        check_existence: True -> check if the file exists, and if safe does not exist return None, False -> do not check.

    Returns:
        The absolute path to the SAFE product if found, otherwise None or the
        path with the unresolved wildcard.
    """
    # check that safe_basename matches expected SAFE pattern
    if not check_safe_name_match_expected_s1_pattern(
        safe_basename.replace(".zip", "")
    ):
        logging.error(
            "The provided SAFE basename does not match the expected Sentinel-1 pattern: %s",
            safe_basename,
        )
        return None
    # Using endswith is more robust than 'in' for checking file extensions.
    if not safe_basename.endswith(".SAFE"):
        safe_basename += ".SAFE"

    # try:
    archive_base_dir = which_archive_dir(
        safe_basename, archive_name=archive_name
    )
    # except Exception as e:
    #     logging.error(
    #         "Could not determine archive directory for %s: %s",
    #         safe_basename,
    #         e,
    #     )
    #     return None

    final_path = os.path.join(archive_base_dir, safe_basename)

    if "*" in final_path:
        # "Look Before You Leap" approach is often clearer for this use case.
        matching_files = glob.glob(final_path)
        if matching_files:
            # If matches are found, return the first one.
            return matching_files[0]
        else:
            # If no match, log a warning and return the path with the wildcard.
            logging.debug("No file found matching pattern: %s", final_path)
            return final_path
    if check_existence:
        if not os.path.exists(final_path):

            # try to replace the unique product ID of the SAFE name because a
            # single acquisition can be processed several times
            inst = ExplodeSAFE(safe_basename)
            product_id = inst.get("product_id")
            safe_name_wildcard = safe_basename.replace(product_id, "*")
            safe_path_wildcard = os.path.join(
                archive_base_dir, safe_name_wildcard
            )
            pot_wild = sorted(glob.glob(safe_path_wildcard))
            if len(pot_wild) > 0:
                final_path = pot_wild[0]  # arbitraril take first one
            else:
                logging.debug("SAFE file does not exist: %s", final_path)
                final_path = None
    # If no wildcard, just return the constructed path.
    return final_path
