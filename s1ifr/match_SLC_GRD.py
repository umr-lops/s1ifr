#!/usr/bin/python
import datetime
import glob
import logging
import os

from s1ifr.explodesafename import ExplodeSAFE
from s1ifr.get_path_from_base_safe import get_path_from_base_safe


def core_find(fp, minimal_time_diff, res_base, startdate):
    """
    return the safe if it exists at Ifremer otherwise None

    Arguments
        fp: str full path of the SAFE to test
        minimal_time_diff: int in seconds
        res_base: str radical of the SAFE pattern to replace in original SAFE
        startdate: datetime.datime of the input product

    Returns
        goodsafe str or None, full path of the SAFE if found otherwise None
    """
    mini_ecart = datetime.timedelta(seconds=15)
    goodsafe = None
    base = os.path.basename(fp)
    pattern = fp.replace(base, res_base)
    pot = glob.glob(pattern)
    for safe in pot:
        logging.debug("potential safe %s", safe)
        basesafel1 = os.path.basename(safe)
        instance = ExplodeSAFE(basesafel1)
        l1st = instance.get("startdate")
        # l1ee = instance.get('enddate')
        #         if l1st<=st and l1ee>=ee:
        if abs(startdate - l1st) < mini_ecart:
            mini_ecart = abs(startdate - l1st)
            if mini_ecart < datetime.timedelta(seconds=minimal_time_diff):
                goodsafe = safe
    return goodsafe


def match_slc_grd(
    safenameslc, type_input="SLC_", type_seek="GRDH", minimal_time_diff=3
) -> str:
    """
    return the safe if it exists at Ifremer otherwise None

    params: safenameslc str
    params: type_input str 'SLC_' or 'GRDH'
    params: type_seek str 'GRDH' or 'SLC_'
    params: minimal_time_diff int in seconds

    returns
        goodsafe str or None, full path of the SAFE if found otherwise None
    """
    res = safenameslc.replace(type_input, type_seek)
    obj = ExplodeSAFE(res)
    st = obj.get("startdate")
    res_base = res[0:10] + "*.SAFE"
    logging.debug("res: %s", res)
    # fp = get_path_from_base_SAFE.get_path_from_base_SAFE(res)
    fp = get_path_from_base_safe(res, archive_name="datawork")
    goodsafe = core_find(fp, minimal_time_diff, res_base, startdate=st)
    if goodsafe is None:
        fp = get_path_from_base_safe(res, archive_name="scale")
        goodsafe = core_find(fp, minimal_time_diff, res_base, startdate=st)
    return goodsafe
