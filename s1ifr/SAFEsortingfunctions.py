"""
@author: A Grouazel
#oct 2014
@purpose: from a safe filename it gives the right path to the ESL FTP dir
"""

import datetime
import logging
import os

from s1ifr.explodesafename import ExplodeSAFE
from s1ifr.utils import load_config


def which_archive_dir(safe, archive_name="datawork",config_path=None):
    """
    Args:
        safe (str): safe base name
        config_path (str): full path of config file .yml for s1ifr [optional]
    """
    conf = load_config(config_path=config_path)
    sats_acro = conf["satellites"]["longnames"]
    datarmor_archive_esa_ifremer = conf["paths"]["datawork"]["archive_esa"]
    scale_archive_esa_ifremer = conf["paths"]["scale"]["archive_esa"]
    datawork_provider = conf["paths"]["datawork"]["project_provider"]

    ADDITIONAL_ARCHIVES = {
        "datawork": datarmor_archive_esa_ifremer,
        "scale": scale_archive_esa_ifremer,
    }
    if safe[0:2] == "S1":
        firstdate = safe[17:25]
        year = firstdate[0:4]
        doy = str(
            datetime.datetime.strptime(firstdate, "%Y%m%d").timetuple().tm_yday
        ).zfill(3)
        mode = safe.split("_")[1]  # IW, EW, SM, WV, OCN
        logging.debug("mode %s", mode)
        sat = safe.split("_")[0]
        sat_letter = sat[2:3]
        satdir = sats_acro[sat]
        acqui = safe.split("_")[1]
        if acqui[0] == "S":
            acqui = "SM"
        level = safe[12:13]
        subproddir = "L" + level
        logging.debug("subproddir %s", subproddir)
        repdata = ADDITIONAL_ARCHIVES[archive_name]
        subname = safe[6:14]
        litlerep = sat + "_" + acqui + subname
        if (
            (mode == "IW" or mode == "EW")
            and subproddir == "L2"
            and sat_letter == "A"
        ):
            # new storage for TOPS OCN managed by CERSAT Dec 2025
            logging.debug("new storage for TOPS OCN managed by CERSAT")
            gooddir = os.path.join(
                datawork_provider.format(satellite=sat_letter.lower()),
                litlerep.lower(),
                year,
                doy + "/",
            )
        else:
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


def which_spool_dir(safe=None, archive="datawork",config_path=None):
    """
    Args:
        safe (str): safe basename with .SAFE extension
        archive (str):datawork or scale
        config_path (str): full path of config file .yml for s1ifr [optional]
    """
    conf = load_config(config_path=config_path)
    WORKING_DIR_DATAWORK = conf["paths"]["datawork"]["workspace"]
    WORKING_DIR_SCALE = conf["paths"]["scale"]["workspace"]

    WORKING_DIR = {"datawork": WORKING_DIR_DATAWORK, "scale": WORKING_DIR_SCALE}
    SPOOL_REP = {  # deprecated
        "datawork": "spool_datarmor/",
        "scale": "spool",
    }
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


def whichquarantinedir(archive="datawork",config_path=None):
    """
    Args:
        archive (str): [optionnal]
        config_path (str): full path of config file .yml for s1ifr [optional]
    Returns:
        str: path of the quarantine directory
    """
    # I want the quarantine to be always on datawork even for product fetch to scale
    conf = load_config(config_path=config_path)
    quarantine_s1 = conf["paths"]["datawork"]["quarantine"]
    return quarantine_s1


if __name__ == "__main__":
    # remove handlers loggging
    logging.getLogger().handlers = []

    logging.basicConfig(level=logging.DEBUG)
    test = "S1A_IW_RAW__0SDV_20140526T145627_20140526T145655_000770_000BAE_BC53.SAFE"
    # test = 'S1A_IW_OCN__2SSH_20220512T035031_20220512T035056_043172_0527ED_2612.SAFE'
    test = "S1C_WV_SLC__1SSV_20250124T170604_20250124T171016_000725_000941_3B92.SAFE"
    print(test)
    print("spool", which_spool_dir(test))
    tmp = which_archive_dir(test)
    print("archive", tmp)
    assert os.path.exists(
        os.path.join(tmp, test)
    ), f"SAFE {os.path.join(tmp, test)} does not exist"
    print("success", os.path.join(tmp, test))
