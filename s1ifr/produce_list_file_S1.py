"""
author: Antoine Grouazel
purpose: optimized tool to produce different kind of Sentinel-1 files list (measurement,SAFE)
 depending on various query arguments (mode,polarisation,level,archive,...)
creation: 2014
"""

import datetime
import fnmatch
import getpass
import glob
import logging
import os

from dateutil import rrule
from tqdm import tqdm

from s1ifr.SAFEsortingfunctions import ADDITIONAL_ARCHIVES
from s1ifr.shared_information import sats_acro,EXTENSIONS


def write_measurement_list(
    type,
    format,
    repdata,
    startdate,
    enddate,
    satellite,
    level,
    onlyonsea=True,
    write_to_file=True,
):
    """
    create a list of measurement file from mpc ifremer sentinel1 archive

    Args:
        type (str): acquisition mode ex : WV
        format (str): ex:slc or grdh or grdm or ocn_
        repdata (str): path up to level directory (included)
        startdate (str): YYYYMMDD
        enddate (str): YYYYMMDD
        satellite (str): S1A or S1B
        level (str): L1 or L2
        onlyonsea (bool): use landmask to keep only acquisition with at least one point on the sea
        write_to_file (bool): [default True]
    """
    format_safe = format.rjust(4, "_")
    format_file = format
    subtype = (
        satellite
        + "_"
        + type
        + "_"
        + format_safe.upper()
        + "_"
        + level[1]
        + "S"
    )
    repdatatype = os.path.join(repdata, type, subtype)
    logging.debug("rep %s", repdatatype)
    extension = EXTENSIONS[level]
    user_run = getpass.getuser()
    filout = os.path.join("/home1/scratch/", user_run)
    pattern = (
        satellite.lower() + "*" + format_file[0:3].lower() + "*." + extension
    )
    logname = (
        satellite
        + "_"
        + type
        + "_"
        + format_safe
        + "_"
        + startdate
        + "_"
        + enddate
        + "_"
        + extension
        + "_onsea_"
        + str(onlyonsea)
        + ".lst"
    )
    startdate = datetime.datetime.strptime(startdate, "%Y%m%d")
    enddate = datetime.datetime.strptime(enddate, "%Y%m%d")
    if startdate == enddate:
        enddate += datetime.timedelta(hours=24)
    tifflist = []
    logpath = None
    for dd in rrule.rrule(rrule.DAILY, dtstart=startdate, until=enddate):
        yy = str(dd.year)
        doy = str(dd.timetuple().tm_yday).zfill(3)
        repdatatype_date = os.path.join(repdatatype, yy, doy + "/")
        for root, dirnames, filenames in os.walk(repdatatype_date):
            for filename in fnmatch.filter(filenames, pattern):
                fullpath = os.path.join(root, filename)
                datesar = filename.split("-")[4]
                datesar = datetime.datetime.strptime(datesar, "%Y%m%dt%H%M%S")
                if datesar >= startdate and datesar <= enddate:
                    tifflist.append(fullpath)
    if write_to_file is True:
        logpath = filout + logname
        fid = open(logpath, "w")
        for uu in tifflist:
            fid.write(uu + "\n")
        fid.close()
        logging.info("output %s", logpath)
    return logpath, tifflist


def list_safe_s1_ifr_fs(
    startdate,
    enddate,
    satellite,
    level,
    write=True,
    mode=None,
    formato=None,
    archive_name="datarmor_mpc",
    categories=["S"],
    logfile_path=None,
    logdir_path=None,
):
    """
    create a list of SAFE directories (basename of the SAFE only)
    Args:
        satellite (str): S1A or S1B
        startdate (str): YYYYMMDD
        level (str): L1 or L2 or L0
        write (bool): True -> write product list to a file
        enddate (str): YYYYMMDD
        mode (str): IW EW SM or WV [optional, default all modes "IW", "EW", "SM", "WV"]
        formato (str): e.g. OCN_ SLC_ GRDH RAW_ [optional, default all product types tested]
        archive_name (str): "datarmor_mpc" for instance
        categories (list):  of string 'S', 'A'  or 'N' [default is S=standard]
        logfile_path (str): [optional]
        logdir_path (str): [optional]
    Returns:
        list_safe (list):
        logpath (str):
    """
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    repdata = os.path.join(root_archive, sats_acro[satellite], level + "/")
    logging.debug("repdata= %s", repdata)
    logging.debug("mode=%s", mode)
    if mode is None:
        modes = ["IW", "EW", "SM", "WV"]
    else:
        modes = [mode]
    list_safe = []
    for mode_known in modes:
        repdatatype = os.path.join(repdata, mode_known + "/")
        if os.path.exists(repdatatype):
            for cat in categories:
                prodtype_list = []
                if (
                    formato is None
                ):  # case SLC or GRD (for instance) -> test all format for mode/level
                    list_format = os.listdir(repdatatype)

                    for uu in list_format:
                        if uu[-1] in cat:
                            prodtype_list.append(uu)
                else:

                    known_format = (
                        satellite
                        + "_"
                        + mode_known
                        + "_"
                        + format
                        + "_"
                        + level[1]
                        + cat
                    )
                    prodtype_list.append(known_format)
                for one_format in prodtype_list:
                    repdatatype = os.path.join(repdata, one_format + "/")
                    logging.info("rep %s", repdatatype)
                    extension = "SAFE"
                    pattern = satellite + "*." + extension
                    logging.debug("pattern: %s", pattern)
                    startdate = datetime.datetime.strptime(startdate, "%Y%m%d")
                    enddate = datetime.datetime.strptime(enddate, "%Y%m%d")
                    dates_to_parse = [
                        dd
                        for dd in rrule.rrule(
                            rrule.DAILY, dtstart=startdate, until=enddate
                        )
                    ]
                    for di in tqdm(range(len(dates_to_parse))):
                        d = dates_to_parse[di]
                        year_str = str(d.year)
                        doy = str(d.timetuple().tm_yday).zfill(3)
                        rep_dated = os.path.join(
                            repdatatype, year_str, doy + "/"
                        )
                        logging.debug("rep_dated %s", rep_dated)
                        list_safe = list_safe + glob.glob(rep_dated + pattern)
        else:
            raise OSError(
                f"{repdatatype} path doesnt exist or is not reachable"
            )

    list_safe.sort()
    if write:
        if logfile_path is None:
            if logdir_path is None:
                user_run = getpass.getuser()
                dirout = os.path.join(
                    "/home1/scratch/", user_run, "PRUN_workspace"
                )
            else:
                dirout = logdir_path
            logname = (
                satellite + "_" + startdate + "_" + enddate + "_dirSAFE.lst"
            )
            logpath = os.path.join(dirout, logname)
        else:
            if logdir_path is None:
                logpath = logfile_path
            else:
                logname = (
                    satellite
                    + "_"
                    + startdate
                    + "_"
                    + enddate
                    + "_dirSAFE.lst"
                )
                logpath = os.path.join(logdir_path, logname)
        fid = open(logpath, "w")
        for safe in list_safe:
            fid.write(safe + "\n")
        fid.close()
        logging.info("output %s", logpath)
    else:
        logpath = None
    logging.info("%s SAFE found", len(list_safe))
    return list_safe, logpath


def find_netcdf_day_before(nbdays, satellite, archive_name="mpc"):
    """
    browse Ifremer repositories to find the netCDF data from the X past days
    Args:
        nbdays (int): number of days to take into account before the present day
        satellite (str): sentinel-1a
        archive (str): mpc or benguela or canaries or swarp
    Returns:
        netcdf_list (list):
    """
    logging.info("coloc for a given date %s days back", nbdays)
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    rep_data = os.path.join(root_archive, satellite, "L2/")
    now = datetime.datetime.now()
    yerterday = now - datetime.timedelta(days=nbdays)
    dateyes = datetime.datetime.strftime(yerterday, "%Y%m%d")
    logging.info("find all the %s netCDF on day %s", satellite, dateyes)
    pattern_nc = os.path.join(
        rep_data + "*",
        "*",
        "*",
        "*",
        "*",
        "measurement",
        "*ocn-*" + dateyes + "*.nc",
    )
    logging.debug("pattern %s", pattern_nc)
    netcdf_list = glob.glob(pattern_nc)
    logging.info("number of netCDF found %s", len(netcdf_list))
    return netcdf_list


def find_netcdf_between_2_dates(
    start, stop, satellite, mode="*", archive_name="datarmor_mpc"
) -> list:
    """
    start,stop (datetime)
    satellite (str) sentinel-1a or 1b
    mode (str): WV IW EW SM [default all]
    archive (str): mpc or benguela or canaries or swarp

    :returns
        netcdf_list (list):
    """
    logging.debug(
        "looking for SAR netcdf files between %s-%s dates", start, stop
    )
    netcdf_list = []
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    rep_data = os.path.join(root_archive, satellite, "L2/")

    start_rule = start - datetime.timedelta(
        days=1
    )  # added 26 nov 2021, because some nc are in SAF that belongs to previous day
    if start > stop:
        raise ValueError("start date is > stop date")
    if start == stop:
        stop = stop + datetime.timedelta(days=1)
    cpt = 0
    cpt_out_of_bounds = 0
    logging.debug("start = %s,stop = %s,stop = %s", start, stop, stop)
    for dd in rrule.rrule(rrule.DAILY, dtstart=start_rule, until=stop):
        year = str(dd.year)
        doy = str(dd.timetuple().tm_yday).zfill(3)
        dateyes = datetime.datetime.strftime(dd, "%Y%m%d")
        pattern_nc = os.path.join(
            rep_data,
            mode,
            "*",
            year,
            doy,
            "*" + dateyes + "*.SAFE",
            "measurement",
            "*ocn-*.nc",
        )
        if cpt == 0:
            logging.debug("first pattern tested = %s", pattern_nc)
        tmp = glob.glob(pattern_nc)
        logging.debug("pattern %s : %s", pattern_nc, len(tmp))

        for ff in tmp:
            datestartdt = datetime.datetime.strptime(
                os.path.basename(ff).split("-")[4], "%Y%m%dt%H%M%S"
            )
            if datestartdt >= start and datestartdt <= stop:
                netcdf_list.append(ff)
            else:
                cpt_out_of_bounds += 1
        cpt += 1
    logging.debug("number of netCDF found %s", len(netcdf_list))
    logging.debug("cpt_out_of_bounds : %s", cpt_out_of_bounds)
    return netcdf_list


def find_s1_measurement_between_2_dates(
    start, stop, product_type, archive_name="datarmor_mpc"
) -> list:
    """

    list the S1 products in ifremer archive for a time span

    Args:
        start,stop (datetime):
        product_type (str): ex S1A_WV_SLC__1S
    :Returns
        netcdf_list (list)
    """
    netcdf_list = []
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    satellite = product_type[0:3]
    fs = sats_acro[satellite]
    logging.debug("full satellite unit name :%s", fs)
    mode = product_type.split("_")[1]
    level = "L" + product_type[-2:-1]
    if level == "L1":
        ext = "measurement/*.tiff"
    elif level == "L2":
        ext = "measurement/*.nc"
    elif level == "L0":
        ext = "*.dat"
    if start > stop:
        raise ValueError("start date is > stop date")
    logging.debug("start: %s,stop: %s", start, stop)
    #     if current_date == last_date:
    #         last_date = current_date+datetime.timedelta(days=1)
    for dd in tqdm(rrule.rrule(rrule.DAILY, dtstart=start, until=stop)):
        year = str(dd.year)
        doy = str(dd.timetuple().tm_yday).zfill(3)
        patho = os.path.join(
            root_archive, fs, level, mode, product_type, year, doy
        )
        logging.debug("path constructed: %s", patho)
        if os.path.exists(patho):
            pattern = os.path.join(patho, "*.SAFE", ext)
            logging.debug("pattern: %s", pattern)
            tmp = glob.glob(pattern)
            netcdf_list = netcdf_list + tmp
    logging.debug("number of netCDF found %s", len(netcdf_list))
    return netcdf_list


def find_sar_tiff_between_2_dates(
    start,
    stop,
    satellite,
    mode,
    archive_name="datarmor_mpc",
    processing_format="*",
):
    """
    start,stop (str/datetime)
    satellite (str) sentinel-1a or 1b
    mode (list) [IW,EW,...]
    processing_format (str): GRDM or SLC_ or GRDH or GRDF or *
    """
    logging.debug(
        "looking for SAR tiff files between %s-%s dates", start, stop
    )
    if isinstance(mode, str):
        mode = [mode]
    tiff_list = []
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    rep_data = os.path.join(root_archive, satellite, "L1")
    if start > stop:
        raise ValueError("start date is > stop date")
    for dd in rrule.rrule(rrule.DAILY, dtstart=start, until=stop):
        year = str(dd.year)
        doy = str(dd.timetuple().tm_yday).zfill(3)
        dateyes = datetime.datetime.strftime(dd, "%Y%m%d")
        for mm in mode:
            pattern = os.path.join(
                rep_data,
                mm,
                "*_" + processing_format + "_1S",
                year,
                doy,
                "*",
                "measurement",
                "*" + dateyes + "*.tiff",
            )
            tmp = glob.glob(pattern)
            logging.debug("pattern %s : %s", pattern, len(tmp))
            tiff_list = tiff_list + tmp
    logging.debug("number of tiff found %s", len(tiff_list))
    return tiff_list


def findtifffromdaybefore(
    nbdays,
    satellite,
    mode=None,
    archive_name="datarmor_mpc",
):
    """
    browse the mpc repositories to find the tiff data from last days
    mode (str): EW IW SM or WV
    """
    if mode is None:
        modes = ["SM", "IW", "EW", "WV"]
    else:
        modes = [mode]
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    sat_dir = sats_acro[satellite]
    rep_data = os.path.join(root_archive, sat_dir, "L1/")
    ext = "tiff"
    product_type = "1S"
    file_format = "grd"

    now = datetime.datetime.now()
    yerterday = now - datetime.timedelta(days=nbdays)
    dateyes = datetime.datetime.strftime(yerterday, "%Y%m%d")
    logging.info("find all the %s tiff on day %s", satellite, dateyes)
    files_sm = []
    files_iw = []
    files_ew = []
    files_wv = []
    if "SM" in modes:
        files_sm = glob.glob(
            rep_data
            + "SM/"
            + satellite
            + "_SM_*_"
            + product_type
            + "/*/*/*/measurement/*"
            + file_format
            + "-*"
            + dateyes
            + "*."
            + ext
        )
        logging.info("number of tiff found for SM %s", len(files_sm))
    if "IW" in modes:
        files_iw = glob.glob(
            os.path.join(
                rep_data,
                "IW",
                satellite + "_IW_" + file_format.upper() + "_" + product_type,
                "*",
                "*",
                "*",
                "measurement",
                "*" + file_format + "-*" + dateyes + "*." + ext,
            )
        )
        logging.info("number of tiff found for IW %s", len(files_iw))
    if "EW" in modes:
        files_ew = glob.glob(
            os.path.join(
                rep_data,
                "EW",
                satellite + "_EW_" + file_format.upper() + "_" + product_type,
                "*",
                "*",
                "*",
                "measurement",
                "*" + file_format + "-*" + dateyes + "*." + ext,
            )
        )
        logging.info("number of tiff found for EW %s", len(files_ew))
    if "WV" in modes:
        files_wv = glob.glob(
            os.path.join(
                rep_data,
                "WV",
                satellite + "_WV_SLC__" + product_type,
                "*",
                "*",
                "*",
                "measurement",
                "*-slc-*" + dateyes + "*." + ext,
            )
        )
        logging.info("number of tiff found for WV %s", len(files_wv))
    final_list = files_sm + files_iw + files_ew + files_wv
    #     logging.debug('%s',files_list)
    logging.info("number of tiff found %s", len(final_list))
    return final_list


def main():
    logging.basicConfig(level=logging.DEBUG)
    choice_usage = [
        "count_SAFE",
        "count_measurement",
        "count_measurementv2",
        "write_measurment_list",
    ]
    level_choice = ["L1", "L2"]
    format_choice = ["SLC_", "GRDH", "GRDF", "GRDM", "OCN_", "RAW_"]
    satellite_choice = ["S1A", "S1B", "S1C"]
    mode_choice = ["WV", "EW", "IW", "SM"]
    import argparse

    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    possibles_archives = [rere for rere in ADDITIONAL_ARCHIVES]
    parser = argparse.ArgumentParser(description="listS1Products@Ifr")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="verbose mode",
    )
    parser.add_argument(
        "-b",
        "--begining",
        action="store",
        dest="startdate",
        metavar="string",
        required=True,
        help="starting date YYYYMMDD",
    )
    parser.add_argument(
        "-e",
        "--enddate",
        action="store",
        dest="enddate",
        metavar="string",
        required=True,
        help="stoping date YYYYMMDD",
    )
    parser.add_argument(
        "-u",
        "--usage",
        action="store",
        choices=choice_usage,
        dest="usage",
        metavar="string",
        help=f"what do you want: {choice_usage} ?",
    )
    parser.add_argument(
        "-l",
        "--level",
        action="store",
        choices=level_choice,
        dest="level",
        metavar="string",
        required=True,
        help=f"which level do you want: {level_choice} ?",
    )
    parser.add_argument(
        "-f",
        "--format",
        action="store",
        choices=format_choice,
        dest="format",
        metavar="string",
        help=f"which format do you want: {format_choice} ?",
    )
    parser.add_argument(
        "-o",
        "--outputlisting",
        action="store",
        dest="outputlisting",
        metavar="string",
        help="file where to write result",
    )
    parser.add_argument(
        "-s",
        "--satellite",
        action="store",
        choices=satellite_choice,
        dest="satellite",
        metavar="string",
        help=f"which satellite do you want: {satellite_choice} ?",
    )
    parser.add_argument(
        "-m",
        "--mode",
        action="store",
        choices=mode_choice,
        dest="mode",
        metavar="string",
        help=f"which mode do you want: {mode_choice} ?",
    )
    parser.add_argument(
        "-a",
        "--archive",
        action="store",
        choices=possibles_archives,
        dest="archive",
        metavar="string",
        help=f"which archive do you want: {ADDITIONAL_ARCHIVES.keys()} ? [optional, default is datarmor_mpc ]",
    )
    args = parser.parse_args()

    startdt = datetime.datetime.strptime(args.startdate, "%Y%m%d")
    stopdt = datetime.datetime.strptime(args.enddate, "%Y%m%d")
    if args.archive is None:
        archive_name = "datarmor_mpc"
    else:
        archive_name = args.archive
    fmt = "%(asctime)s %(levelname)s %(filename)s(%(lineno)d) %(message)s"
    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format=fmt,
            datefmt="%d/%m/%Y %H:%M:%S",
            force=True,
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format=fmt,
            datefmt="%d/%m/%Y %H:%M:%S",
            force=True,
        )
    if args.usage == "count_SAFE":
        list_safe_s1_ifr_fs(
            args.startdate,
            args.enddate,
            args.satellite,
            level=args.level,
            mode=args.mode,
            formato=args.format,
            archive_name=archive_name,
            logfile_path=args.outputlisting,
        )
    elif args.usage == "count_measurement":
        if args.level == "L1":
            tiff_list = find_sar_tiff_between_2_dates(
                startdt,
                stopdt,
                sats_acro[args.satellite],
                [args.mode],
                archive_name=archive_name,
                processing_format=args.format,
            )
            logging.info("Nber of measurement: %s", len(tiff_list))
        elif args.level == "L2":
            netcdf_list = find_netcdf_between_2_dates(
                startdt,
                stopdt,
                sats_acro[args.satellite],
                args.mode,
                archive_name=archive_name,
            )
            logging.info("Nber of measurement: %s", len(netcdf_list))
    elif args.usage == "write_measurment_list":
        sat_dir = sats_acro[args.satellite]
        root_archive = ADDITIONAL_ARCHIVES[archive_name]
        rep_data = os.path.join(root_archive, sat_dir, args.level)
        write_measurement_list(
            args.mode,
            args.format,
            rep_data,
            args.startdate,
            args.enddate,
            args.satellite,
            args.level,
            onlyonsea=False,
            write_to_file=True,
        )
    elif args.usage == "count_measurementv2":  # not better simply more rafined
        product_type = (
            args.satellite
            + "_"
            + args.mode
            + "_"
            + args.format
            + "_"
            + args.level[1]
            + "S"
        )
        logging.info("product type: %s", product_type)
        listmesu = find_s1_measurement_between_2_dates(
            startdt, stopdt, product_type, archive_name="datarmor_mpc"
        )
        print(len(listmesu))
    else:
        raise ValueError("Bad argument usage")


if __name__ == "__main__":

    main()
