"""
@author: A Grouazel
#oct 2014
@purpose: from a safe filename it gives the right path to the ESL FTP dir
"""

import datetime
import logging
import os

from s1ifr.explodesafename import ExplodeSAFE
from s1ifr.shared_information import QUARANTINE as quarantine_s1
from s1ifr.shared_information import (
    WORKING_DIR,
    WORKING_DIR_SCALE,
    datarmor_archive_esa_ifremer,
    sats_acro,
    scale_archive_esa_ifremer,
)

ADDITIONAL_ARCHIVES = {
    "datawork": datarmor_archive_esa_ifremer,
    "scale": scale_archive_esa_ifremer,
}
WORKING_DIR = {"datawork": WORKING_DIR, "scale": WORKING_DIR_SCALE}
SPOOL_REP = {  # deprecated
    "datawork": "spool_datarmor/",
    "scale": "spool",
}


def which_archive_dir(safe, archive_name="datawork"):
    """
    Args:
        safe (str): safe base name
    """
    if safe[0:2] == "S1":
        firstdate = safe[17:25]
        year = firstdate[0:4]
        doy = str(
            datetime.datetime.strptime(firstdate, "%Y%m%d").timetuple().tm_yday
        ).zfill(3)
        sat = safe.split("_")[0]
        satdir = sats_acro[sat]
        acqui = safe.split("_")[1]
        if acqui[0] == "S":
            acqui = "SM"
        level = safe[12:13]
        subproddir = "L" + level
        repdata = ADDITIONAL_ARCHIVES[archive_name]
        subname = safe[6:14]
        litlerep = sat + "_" + acqui + subname
        gooddir = os.path.join(
            repdata, satdir, subproddir, acqui, litlerep, year, doy + "/"
        )
    elif safe[0:2] == "S3":  # sentinel-3 case
        inst = ExplodeSAFE(safe)
        year = inst.startdate.strftime("%Y")
        doy = inst.startdate.strftime("%j")
        gooddir = os.path.join(ADDITIONAL_ARCHIVES["s3sral"], year, doy)
    else:
        raise ValueError("no handled product mission")
    return gooddir


def which_spool_dir(safe=None, archive="datawork"):
    """
    Args:
        safe (str): safe basename with .SAFE extension
        archive (str):datawork or scale
    """
    if safe is None:
        # default is spool sentinel1
        spooldir = os.path.join(WORKING_DIR[archive], SPOOL_REP[archive])
    else:
        if safe[0:2] == "S1":
            spooldir = os.path.join(WORKING_DIR[archive], SPOOL_REP[archive])
            spooldir = os.path.join(
                spooldir
            )  # change this to get a real spool where the product can be drop easily

        else:
            raise ValueError(f"safe {safe} doesnt start with S1")
    return spooldir


def whichquarantinedir(archive="datawork"):
    """
    Args:
        archive (str):
    """
    # res = quarantine_s1[archive]
    res = quarantine_s1[
        "datawork"
    ]  # I want the quarantine to be always on datawork even for product fetch to scale
    return res


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test = "S1A_IW_RAW__0SDV_20140526T145627_20140526T145655_000770_000BAE_BC53.SAFE"
    print(test)
    print("spool", which_spool_dir(test))
    tmp = which_archive_dir(test)
    print("archive", tmp)
