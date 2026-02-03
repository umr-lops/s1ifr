"""
Author: Antoine Grouazel
creation: june2014
check that S1 Level 0 and Level1 data is not corrupted
#TODO: check also Level2!!!
"""

import collections
import datetime
import fnmatch
import hashlib
import logging
import os
import shutil
import traceback
from xml.dom import minidom

from s1ifr.produce_list_file_S1 import list_safe_s1_ifr_fs
from s1ifr.utils import give_me_level_from_type, load_config

SECURITY_SECONDS = 300
table_subdir_subprod = {
    "L0S": ("support"),
    "L0C": ("support"),
    "L0N": ("support"),
    "L0A": ("support"),
    "L1S": ("annotation", "measurement", "preview", "support"),
    "L1A": ("annotation", "preview", "support"),
    "L2A": ("annotation", "preview", "support"),
    "L2S": ("measurement", "preview", "support"),
}


def check_safe_sentinel3(full_path_safe):
    """
    proto checker for Sentinel-3 SRAL
    """
    safe_is_ok = True
    enhan = os.path.join(full_path_safe, "enhanced_measurement.nc")
    redu = os.path.join(full_path_safe, "reduced_measurement.nc")
    stand = os.path.join(full_path_safe, "standard_measurement.nc")
    xfd = os.path.join(full_path_safe, "xfdumanifest.xml")

    if not os.path.exists(enhan):
        safe_is_ok = False
    if not os.path.exists(redu):
        safe_is_ok = False
    if not os.path.exists(stand):
        safe_is_ok = False
    if not os.path.exists(xfd):
        safe_is_ok = False

    return safe_is_ok


def delete_corrupted_safe(corrupted_list, dirout) -> int:
    """

    :param corrupted_list: list
    :param dirout: str directory where to list the SAFE removed
    :return:
    """
    logging.info("read %s to delete spotted corrupted SAFE", corrupted_list)
    current_time = datetime.datetime.strftime(
        datetime.datetime.now(), "%Y%m%d_%Hh%M"
    )
    logout = dirout + "deleted_" + current_time + ".lst"
    fod = open(corrupted_list)
    lines = fod.readlines()
    fod.close()
    cpt = 0
    if len(lines) > 0:
        fid = open(logout, "w")
        for line in lines:
            if " " in line:
                safe_path = line.split(" ")[0]
                reason = line.split(" ")[1]
            else:
                safe_path = line.replace("\n", "")
                reason = "unknown"
            logging.info("deleting corrupted %s because %s", safe_path, reason)
            if os.path.exists(safe_path):
                try:
                    shutil.rmtree(
                        safe_path
                    )  # we do not remove anything, only # feb2019 too much data: we need to remove corrupted SAFE (taking the risk of fake positive cases)
                #                     os.system('/bin/mv -f '+safe_path+' '+QUARANTINE) #put in quarantine rather than deletion
                except OSError:
                    logging.info(
                        "error during the suppression of the SAFE: %s",
                        traceback.format_exc(),
                    )
                    logging.info(
                        "impossible to delete this SAFE: %s", safe_path
                    )
                cpt += 1
            else:
                logging.info(
                    "it seems that %s does not exist anymore", safe_path
                )
            fid.write(safe_path + "\n")
        fid.close()
    return cpt


def check_number_of_measurement(manifestpath) -> bool:
    """
    return true if the number of measurement is in line with manifest file

    Arguments:
        manifestpath (str): full path of the manifest.safe file

    :returns:
        all_measu_present (bool): True -> valid product
    """
    logging.debug("manifest.safe : %s", manifestpath)
    try:
        xmlcontent = minidom.parse(manifestpath)
        dir_name = os.path.dirname(manifestpath)
        meas = xmlcontent.getElementsByTagName("fileLocation")
        all_measu_present = True
        for occur in meas:
            dat_file_name = occur.getAttribute("href")
            if "measurement" in dat_file_name:
                meas_path = os.path.join(dir_name, dat_file_name)
                logging.debug("measurement file to read %s", meas_path)
                if not os.path.exists(meas_path):
                    logging.warning("file  %s doesnt exist", meas_path)
                    all_measu_present = False
    except OSError:
        logging.error("traceback %s", traceback.format_exc())
        logging.error("cant parse manifest %s ", manifestpath)
        all_measu_present = False

    logging.debug("test number of tiff: %s", all_measu_present)
    return all_measu_present


def check_presence_of_manifest_file(manifestpath):
    """
    return True if the manifest is present

    Args:
        manifestpath (str): full path of the manifest.safe
    """
    if os.path.exists(manifestpath) is False:
        logging.info("manifest.safe %s doesnt exist", manifestpath)
        manifestfileok = False
    else:
        manifestfileok = True
    logging.debug("test manifest %s", manifestfileok)
    return manifestfileok


def exploit_check_sum(safepath):
    """use the checksum value of manifest file to control that the data is not corrupted"""

    flag = True
    manifestpath = os.path.join(safepath, "manifest.safe")
    xmlcontent = minidom.parse(manifestpath)
    check_sums_values = xmlcontent.getElementsByTagName("checksum")
    files_path = xmlcontent.getElementsByTagName("fileLocation")
    for jj, cc in enumerate(check_sums_values):
        dat_file_name = files_path[jj].getAttribute("href")
        md5_official = cc.firstChild.nodeValue

        # find the corresponding data file
        dat_file_path = os.path.join(safepath, dat_file_name)
        md5 = hashlib.md5(open(dat_file_path).read()).hexdigest()
        if md5 != md5_official:
            flag = False
            logging.debug(
                "corruption checksum %s path %s, md5 got %s",
                md5_official,
                dat_file_path,
                md5,
            )
    logging.debug("exploit_check_sum %s", flag)
    return flag


def check_sub_directories(safe_path, level, typefile):
    """return True if all sub dir are present"""
    res = True

    tmp = table_subdir_subprod["L" + level + typefile]
    #     logging.debug('tmp dir names type %s %s',type(tmp),isinstance(tmp, basestring))
    if isinstance(tmp, str):
        tmp = [tmp]
    list_of_dir_mandatory = tmp
    for dir in list_of_dir_mandatory:
        logging.debug("dir %s", dir)
        if not os.path.exists(os.path.join(safe_path, dir)):
            logging.info("directory %s doesnt exist in %s", dir, safe_path)
            res = False
    logging.debug("test subdirs %s", res)
    return res


def write_to_log(logpath, test_name, safe_path):
    file_handler = open(logpath, "a")
    file_handler.write(safe_path + " " + test_name + " \n")
    file_handler.close()


def safe_checker(
    safe_path, logpath, enable_checksum=False, security_time=SECURITY_SECONDS
) -> bool:
    """
    test one given SAFE
    SAFE is ok by default to avoid lots of deletions (for examplt if the
    Args:
        safe_path (str): full path of SAFE product
        file_handler (int): file handler to write logs
        security_time (int): nber of seconds to wait before checking [optional]
    Return:
        flag_ok_safe (bool): True if the SAFE is OK, False if it is corrupted
    """
    flag_ok_safe = True

    safe_path = safe_path.rstrip("/")
    t = os.path.getctime(safe_path)
    filename = os.path.basename(safe_path)
    logging.debug("test %s", filename)
    nownow = datetime.datetime.today()
    creation_date = datetime.datetime.fromtimestamp(t)
    if nownow - creation_date > datetime.timedelta(seconds=security_time):
        level = os.path.basename(safe_path)[12:13]
        typefile = os.path.basename(safe_path)[13:14]
        logging.debug("level %s", level)
        manifestpath = os.path.join(safe_path, "manifest.safe")

        if check_presence_of_manifest_file(manifestpath) is False:
            write_to_log(logpath, "missingmanifest", safe_path)
            flag_ok_safe = False
            logging.info("manifest test: KO")
        else:
            logging.info("manifest test: OK")

        if check_number_of_measurement(manifestpath) is False:
            write_to_log(logpath, "missingmeasurement", safe_path)
            flag_ok_safe = False
            logging.info("measurement count test: KO")
        else:
            logging.info("measurement count test: OK")

        if check_sub_directories(safe_path, level, typefile) is False:
            write_to_log(logpath, "missingsubdir", safe_path)
            flag_ok_safe = False
            logging.info("sub dirs test: KO")
        else:
            logging.info("sub dirs test: OK")
        if enable_checksum is True:
            if (
                exploit_check_sum(safe_path) is False
            ):  # commented since I had memory error
                write_to_log(logpath, "checksum discrepancy", safe_path)
                flag_ok_safe = False
                logging.info("checksum test: KO")
            else:
                logging.info("checksum test: OK")
        if flag_ok_safe is False:
            logging.info("%s is KO", filename)
        else:
            logging.debug("%s is OK", filename)
    else:
        logging.info(
            "%s has been created less than %s seconds ago",
            filename,
            SECURITY_SECONDS,
        )
    return flag_ok_safe


def log_path(config_path=None):
    """
    return a file where to log products that are not nominal.

    Args:
        config_path (str): full path of config file .yml for s1ifr [optional]

    Returns:
        list_safe_having_problem (str): path of .lst file
    """
    conf = load_config(config_path=config_path)
    dir_suspect = conf["paths"]["scratch"]["satwave"]
    now = datetime.datetime.now()
    now_character = now.strftime("%Y-%m-%d_%Hh%M%S%f")
    list_safe_having_problem = os.path.join(
        dir_suspect, "list_safe_having_problem_" + now_character + ".lst"
    )
    return list_safe_having_problem


def main_loop(
    repdata=None,
    pattern=None,
    unique_safe=None,
    enable_checksum=False,
    list_safe_having_problem=None,
    limit_nb_safe=None,
):
    """

    browse the whole archive to find the pattern


    Args:
        repdata (str):
        pattern (str):
        unique_safe (str):
        enable_checksum (bool):
        limit_nb_safe (int): optional, give the max number of safe analyzed before stoping
        list_safe_having_problem (str): full path

    """
    counters_internal = collections.defaultdict(int)
    status_quality = {}
    if list_safe_having_problem is None:
        list_safe_having_problem = log_path()
    logging.debug("writing suspicious SAFE in %s", list_safe_having_problem)
    cpt_checked = 0
    if unique_safe is not None:

        flag_ok_safe = safe_checker(
            unique_safe, list_safe_having_problem, enable_checksum
        )
        status_quality[unique_safe] = flag_ok_safe
        cpt_checked += 1
    else:
        for root, dirnames, filenames in os.walk(repdata):
            for filename in fnmatch.filter(dirnames, pattern):
                safe_path = os.path.join(root, filename)
                if os.path.isdir(safe_path):
                    cpt_checked += 1
                    flag_ok_safe = safe_checker(
                        safe_path, list_safe_having_problem, enable_checksum
                    )
                    status_quality[safe_path] = flag_ok_safe
                    counters_internal["is_dir"] += 1
                    if counters_internal["is_dir"] % 20 == 1:
                        logging.info("count %s", counters_internal)
                    if limit_nb_safe:
                        if counters_internal["is_dir"] > limit_nb_safe:
                            logging.info(
                                "premature by purpose return with limit_nb_safe %s",
                                limit_nb_safe,
                            )
                            return status_quality
                    if flag_ok_safe:
                        counters_internal["safe_ok"] += 1
                    else:
                        counters_internal["safe_ko"] += 1
                else:
                    counters_internal["is_file"] += 1
                    logging.debug("is a file %s -> no test", safe_path)
    logging.debug("%s SAFE checked", cpt_checked)
    logging.debug("output %s", list_safe_having_problem)
    return status_quality


def main():
    import argparse

    parser = argparse.ArgumentParser(description="quality check S1 SAFE")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument(
        "-c",
        "--checksum",
        action="store_true",
        dest="checksum",
        default=False,
        help="enable the md5 checksum  ",
    )
    parser.add_argument(
        "--configfile",
        help=" path of the s1ifr config file .yml [optional]",
        required=False,
    )
    parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        dest="delete",
        default=False,
        help="delete corrupted product ",
    )
    subparsers = parser.add_subparsers()
    modes = {
        "unique_safe": "analyse a single sentinel-1 SAFE",
        "last_x_days": "analyse the last X days from the current date",
        "between_2_dates": "analyse all the SAFE in a given period",
        "one_safe_s3": "analyse a given sentinel-3 sral safe",
        #              ,'pattern':'browse and analyse all the SAFE matching a given pattern'
    }
    dico_subparsers = {}
    for mm in modes:
        dico_subparsers[mm] = subparsers.add_parser(mm, help=f"{modes[mm]}")
        dico_subparsers[mm].set_defaults(which=mm)
        if mm not in ["unique_safe", "one_safe_s3"]:
            dico_subparsers[mm].add_argument(
                "-m",
                "--mode",
                required=True,
                type=str,
                choices=["IW", "EW", "SM", "WV"],
                help="IW EW SM WV ",
            )
            dico_subparsers[mm].add_argument(
                "-t",
                "--producttype",
                type=str,
                choices=["SLC_", "GRDH", "GRDM", "GRDF", "OCN_", "RAW_"],
                help="SLC_ GRDH GRDM GRDF OCN_ RAW_",
                required=True,
            )
            dico_subparsers[mm].add_argument(
                "--satellite",
                default=None,
                type=str,
                help="satellite S1A or/and ... ",
                nargs="*",
            )
    dico_subparsers["unique_safe"].add_argument(
        "--safepath", help="full path of the SAFE", type=str
    )
    dico_subparsers["one_safe_s3"].add_argument(
        "--safepath", help="full path of the SAFE", type=str
    )
    dico_subparsers["last_x_days"].add_argument(
        "--days_back",
        help="Nber of days to analyse from date of run",
        type=int,
    )
    dico_subparsers["between_2_dates"].add_argument(
        "--start", help="start date YYYYMMDD", type=str
    )
    dico_subparsers["between_2_dates"].add_argument(
        "--stop", help="stop date YYYYMMDD", type=str
    )

    args = parser.parse_args()
    conf = load_config(args.configfile)
    dirdeleted = conf["paths"]["scratch"]["satwave"]
    sats_acro = conf["satellites"]["acronyms"]

    suppression_flag = args.delete
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    list_safe_having_problem = log_path()
    if args.which == "last_x_days" or args.which == "between_2_dates":
        counters = collections.defaultdict(int)
        counters["total"] = 0
        counters["ok"] = 0
        counters["ko"] = 0
        if args.satellite is None:
            satellites = list(sats_acro.keys())
        else:
            satellites = args.satellite
        logging.info("satellites: %s", satellites)
        #     if options.exploitation is not None:
        logging.info(
            "exploit mode : check Sentinel1 SAFE product on the current month"
        )
        for sat in satellites:

            typo = args.mode
            formato = args.producttype
            if args.which == "last_x_days":
                stop = datetime.datetime.today()
                number_of_days_back = int(args.days_back)  # 5 days previously
                start = stop - datetime.timedelta(days=number_of_days_back)
            elif args.which == "between_2_dates":
                start = datetime.datetime.strptime(args.start, "%Y%m%d")
                stop = datetime.datetime.strptime(args.stop, "%Y%m%d")
            logging.info("start: %s stop: %s", start, stop)
            level = give_me_level_from_type(formato)
            list_safe, _ = list_safe_s1_ifr_fs(
                start.strftime("%Y%m%d"),
                stop.strftime("%Y%m%d"),
                satellite=sat,
                level=level,
                write=False,
                mode=typo,
                formato=formato,
            )
            counters["total"] += len(list_safe)
            for sasa in list_safe:
                status = main_loop(
                    unique_safe=sasa,
                    enable_checksum=args.checksum,
                    list_safe_having_problem=list_safe_having_problem,
                )
                if status[sasa]:
                    counters["ok"] += 1
                else:
                    counters["ko"] += 1
        logging.info("counters: %s", counters)
    elif args.which == "unique_safe":
        logging.info("check %s ", args.safepath)
        main_loop(
            unique_safe=args.safepath,
            enable_checksum=args.checksum,
            list_safe_having_problem=list_safe_having_problem,
        )
    elif args.which == "one_safe_s3":
        res = check_safe_sentinel3(full_path_safe=args.safepath)
        logging.info("the safe is OK = %s", res)
    else:
        raise ValueError("this case does not exist")
    if suppression_flag is True and os.path.exists(list_safe_having_problem):
        nb_safe_deleted = delete_corrupted_safe(
            list_safe_having_problem, dirdeleted
        )
        logging.info("Nber of SAFE deleted: %s", nb_safe_deleted)
    # avoid empty log file suspicious
    if os.path.exists(list_safe_having_problem):
        if os.stat(list_safe_having_problem).st_size == 0:
            os.remove(list_safe_having_problem)
            logging.debug("remove empty log")
    logging.info("check complete")


if __name__ == "__main__":

    main()
