#!/usr/bin/python
import datetime
import glob
import logging
import os

from s1ifr.explodesafename import ExplodeSAFE
from s1ifr.get_path_from_base_safe import get_path_from_base_safe


def core_find(fp, minimal_time_diff, res_base, startdate) -> str:
    """Finds the SAFE path if it exists at Ifremer.

    Args:
        fp (str): Full path pattern of the SAFE to test.
        minimal_time_diff (int): Maximum allowed time difference in seconds.
        res_base (str): Radical of the SAFE pattern to replace in original SAFE.
        startdate (datetime.datetime): Start date of the input product.

    Returns:
        str or None: Full path of the SAFE if found, otherwise None.
    """
    mini_ecart = datetime.timedelta(seconds=15)  # default large value
    goodsafe = None
    base = os.path.basename(fp)
    pattern = fp.replace(base, res_base)
    pot = glob.glob(pattern)
    for safe in pot:
        logging.debug("potential safe %s", safe)
        basesafel1 = os.path.basename(safe)
        instance = ExplodeSAFE(basesafel1)
        l1st = instance.get("startdate")

        if abs(startdate - l1st) < mini_ecart:
            mini_ecart = abs(startdate - l1st)
            if mini_ecart < datetime.timedelta(seconds=minimal_time_diff):
                goodsafe = safe
    return goodsafe


def match_slc_grd(
    safenameslc, type_input="SLC_", type_seek="GRDH", minimal_time_diff=3
) -> str:
    """Matches an SLC product with its corresponding GRD (or vice versa).

    Args:
        safenameslc (str): The basename of the SAFE product.
        type_input (str): The type of the input product, e.g., ``"SLC_"`` or ``"GRDH"``.
        type_seek (str): The type of product to search for, e.g., ``"GRDH"`` or ``"SLC_"``.
        minimal_time_diff (int): Maximum time difference in seconds for a valid match.
            Defaults to 3.

    Returns:
        str or None: Full path of the matched SAFE if found in archives, otherwise None.
    """
    assert len(type_input) == 4
    safe_mirrored = safenameslc.replace(type_input, type_seek)
    obj = ExplodeSAFE(safe_mirrored)
    st = obj.get("startdate")
    res_base = safe_mirrored[0:10] + "*.SAFE"
    logging.debug("safe_mirrored: %s", safe_mirrored)

    # Search in datawork
    fp = get_path_from_base_safe(safe_mirrored, archive_name="datawork")
    goodsafe = core_find(fp, minimal_time_diff, res_base, startdate=st)

    # Fallback to scale
    if goodsafe is None:
        fp = get_path_from_base_safe(safe_mirrored, archive_name="scale")
        goodsafe = core_find(fp, minimal_time_diff, res_base, startdate=st)

    return goodsafe
