#!/usr/bin/python
import datetime
import glob
import logging
import os

from s1ifr.explodesafename import ExplodeSAFE
from s1ifr.get_path_from_base_safe import get_path_from_base_safe


def _core_find(
    search_path_pattern: str,
    input_start_date: datetime.datetime,
    time_threshold_sec: int,
) -> str | None:
    """
    Finds the SAFE file with the smallest time difference within a given threshold.

    This is a helper function designed to find the best match in a list of potential files.

    Args:
        search_path_pattern (str): The glob pattern to search for files (e.g., '/path/to/S1A_IW_GRDH*.SAFE').
        input_start_date (datetime.datetime): The start time of the original input product.
        time_threshold_sec (int): The maximum allowed time difference in seconds.

    Returns:
        Optional[str]: The full path to the best matching SAFE file, or None if no suitable match is found.
    """
    potential_matches = glob.glob(search_path_pattern)
    if not potential_matches:
        return None

    best_match_path = None
    # REASON FOR CHANGE: Initialize with a time difference larger than the threshold.
    # This ensures that any valid match will be selected initially.
    best_time_diff = datetime.timedelta(seconds=time_threshold_sec + 1)

    for path in potential_matches:
        logging.debug("Potential safe: %s", path)
        try:
            instance = ExplodeSAFE(os.path.basename(path))
            candidate_start_date = instance.get("startdate")
            current_diff = abs(input_start_date - candidate_start_date)

            # REASON FOR CHANGE: This logic now correctly finds the file with the
            # absolute smallest time difference among all candidates.
            if current_diff < best_time_diff:
                best_time_diff = current_diff
                best_match_path = path
        except Exception as e:
            logging.warning(
                "Could not parse SAFE name '%s': %s", os.path.basename(path), e
            )
            continue

    # REASON FOR CHANGE: The check against the threshold is now done only once,
    # after finding the closest possible match. This is more efficient and correct.
    if best_match_path and best_time_diff.total_seconds() < time_threshold_sec:
        logging.info(
            "Found match %s with time diff of %s seconds",
            os.path.basename(best_match_path),
            best_time_diff.total_seconds(),
        )
        return best_match_path

    return None


def match_slc_grd(
    safename: str,
    type_input: str = "SLC_",
    type_seek: str = "GRDH",
    minimal_time_diff: int = 3,
) -> str | None:
    """
    Finds a matching GRDH or SLC product for a given SAFE file across Ifremer archives.

    It searches first in the 'datawork' archive, then falls back to the 'scale' archive if no
    match is found.

    Args:
        safename (str): The full name of the input SAFE file.
        type_input (str): The type of the input file ('SLC_' or 'GRDH').
        type_seek (str): The type of the file to find ('GRDH' or 'SLC_').
        minimal_time_diff (int): The maximum allowed time difference in seconds.

    Returns:
        Optional[str]: The full path of the matching SAFE file if found, otherwise None.
    """
    try:
        # REASON FOR CHANGE: Parse the original input filename to get the start date.
        # This is safer than parsing a hypothetical filename.
        input_info = ExplodeSAFE(safename)
        input_start_date = input_info.get("startdate")
    except Exception as e:
        logging.error("Could not parse input SAFE name '%s': %s", safename, e)
        return None

    target_safename = safename.replace(type_input, type_seek)
    # REASON FOR CHANGE: A more robust pattern using the first 10 characters
    # (e.g., 'S1A_IW_GRD') to build the glob pattern.
    target_base_pattern = f"{os.path.basename(target_safename)[:10]}*.SAFE"
    logging.debug("Target pattern: %s", target_base_pattern)

    # REASON FOR CHANGE: Loop through archives to avoid repeating code (DRY principle).
    for archive in ["datawork", "scale"]:
        logging.debug("Searching in '%s' archive...", archive)
        base_path = get_path_from_base_safe(
            target_safename, archive_name=archive
        )

        # REASON FOR CHANGE: Use os.path.join for robust path construction.
        search_pattern = os.path.join(
            os.path.dirname(base_path), target_base_pattern
        )

        found_safe = _core_find(
            search_pattern, input_start_date, minimal_time_diff
        )
        if found_safe:
            return found_safe

    logging.warning(
        "No matching product found for %s in any archive.", safename
    )
    return None
