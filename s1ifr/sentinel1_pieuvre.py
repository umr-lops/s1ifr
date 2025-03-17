"""
@name sentinel1_pieuvre
@purpose: uncompress and move S-1 SAFE in the right archive directory from spool
# uncompress
# delete archive from spool
# set permission 775
@author: Antoine Grouazel
@creation: 18 June 2015
@history: 26 nov 2024 adapted from mpc/sentinel1_pieuvre.py
"""

import datetime
import getpass
import logging
import os
import shutil
import subprocess
import time
import traceback

from s1ifr.check_SAFE_files import safe_checker
from s1ifr.clean_sentinel1_duplicates_function import check_duplicate
from s1ifr.existence_safe import product_is_present_at_ifremer
from s1ifr.quarantine_management import (
    quarantine_ticket,
    remove_safe_from_disk,
)
from s1ifr.SAFEsortingfunctions import (
    which_archive_dir,
    which_spool_dir,
)

UNEXISTANT = "unexistant"
NORMAL = "normal"
ALREADY = "already_in"
TOORECENT = "too_recent"
QUARANTINED = "quarantine"  # means that the data is not in the appropriate format and then it is moved to quaarantine
FAILED = "failed"  # mean the script crash

EXTENSION_SAFE = ".SAFE"


def finalize_archiving(
    archive_dir,
    unzipped_safe,
    final_place,
    ziptype="",
    archive_name="mpc",
):
    """
    mv the safe to archive directory then chmod
    Args:
        archive_dir (str):
        unzipped_safe (str): fullpath but without .tar
        final_place (str): the place the safe should be in archive if no corruption
        ziptype (str): .tar or .zip or ''
        archive_name (str):
    """
    #     unziped_safe = full_path_safe.strip('.tar')
    # check that the SAFE uncompressed is not corrupted
    doom_flag = NORMAL
    user_run = getpass.getuser()
    logpath = os.path.join(
        "/home1/scratch", user_run, "sentinel1_quality_check_after_unzip.txt"
    )

    is_ok_safe = safe_checker(
        unzipped_safe, logpath=logpath, security_time=0
    )


    if is_ok_safe:
        cmd = "/bin/mv -f " + unzipped_safe + " " + archive_dir
        logging.debug("command to execute %s", cmd)

        status = subprocess.check_output(cmd, shell=True)
        if status != 0:
            st = os.system("chmod 775 -R " + final_place)
            if st != 0:
                logging.error("chmod operation on %s failed", final_place)
                doom_flag = FAILED
            else:
                logging.debug("chmod done")
        else:
            doom_flag = FAILED
    else:
        logging.error(
            "%s is corrupted, so we delete it to let it be re download",
            unzipped_safe,
        )
        quarantine_ticket(unzipped_safe, archive_name)
        doom_flag = QUARANTINED
    original_full_path = unzipped_safe + ziptype
    logging.debug("original_full_path = %s", original_full_path)
    # remove the tar or zip file that is now useless since uncompress has been done or move to quarantine
    if os.path.exists(original_full_path) is True:
        logging.info("%s has been deleted ", original_full_path)
        if os.path.isdir(original_full_path):
            shutil.rmtree(original_full_path)
        else:
            os.remove(original_full_path)
    return doom_flag


def sort_one_safe(
    full_path_safe,
    log_file_handler=None,
    other_archive="datawork",
    security_second=600,
    dryrun=False,
):
    """
    :input:
        full_path_safe (str): can be anywhere with or without .tar extension
        log_file_handler (int): [optional]
        other_archive (str) : name of the archive where to store the file [optional]
        security_second (int): number minimum of seconds since last modification [optional]
        dryrun (bool): do not uncompress nor move the product
    :output:
        doom_flag (str): tell what appended to the SAFE treated
        cpt_dupli (int): counter of duplicate
    """
    if full_path_safe[-1] == "/":
        full_path_safe = full_path_safe[0:-1]
    logging.debug("sentinel1_pieuvre | start analysis of %s", full_path_safe)
    doom_flag = FAILED
    cpt_dupli = 0
    final_place = None
    if os.path.exists(full_path_safe):
        if log_file_handler is None:
            logging.debug(
                "sentinel1_pieuvre | note that the SAFE you want to sort and store will not be log"
            )
        if ".tar" in full_path_safe:
            safe_basename = os.path.basename(full_path_safe.strip(".tar"))
        elif ".zip" in full_path_safe:
            safe_basename = os.path.basename(full_path_safe.strip(".zip"))
        else:
            safe_basename = os.path.basename(
                full_path_safe.replace(".SAFE/", EXTENSION_SAFE)
            )
        if safe_basename[0:2] == "S1" and safe_basename[-5:] != EXTENSION_SAFE:
            safe_basename = safe_basename + EXTENSION_SAFE
        logging.debug("basename : %s", safe_basename)
        archive_dir = which_archive_dir(
            safe_basename, archive_name=other_archive
        )
        final_place = os.path.join(archive_dir, safe_basename)
        if dryrun is True:
            logging.info("final path should be %s", final_place)
        else:
            logging.debug("final path should be %s", final_place)
        flag_continue, _, _ = product_is_present_at_ifremer(
            safe_basename, full_path_safe
        )
        if flag_continue is True and dryrun is False:

            os.makedirs(archive_dir, 0o0775, exist_ok=True)
            t = os.path.getctime(full_path_safe)
            creation_date = datetime.datetime.fromtimestamp(t)
            nownow = datetime.datetime.today()
            seconds_since_creation = nownow - creation_date
            logging.debug(
                "%1.2fseconds elapsed since file downloaded",
                seconds_since_creation.total_seconds(),
            )
            # second security
            taille1 = os.path.getsize(full_path_safe)
            time.sleep(1)
            taille2 = os.path.getsize(full_path_safe)
            if (
                seconds_since_creation
                >= datetime.timedelta(seconds=security_second)
                and taille1 == taille2
            ):
                if log_file_handler is not None:
                    log_file_handler.write(full_path_safe + "\n")
                if full_path_safe.endswith(".tar"):
                    logging.debug(
                        "classical case",
                    )
                    spool_dir = which_spool_dir(
                        safe_basename, archive=other_archive
                    )
                    os.chdir(spool_dir)
                    st = os.system("tar xf " + full_path_safe)
                    unziped_safe = full_path_safe.strip(".tar")
                    if st != 0 or os.path.exists(unziped_safe) is False:
                        logging.error(
                            "uncompress operation on %s failed status = %s",
                            full_path_safe,
                            st,
                        )
                        # in this case the tar is kept because we are not sure that the tar itself is broken => risk of stagging tar ??
                        #                         raise Exception('fail to uncompress %s so it will be removed from spool',full_path_safe)
                        print(traceback.format_exc())
                        #                         shutil.move(full_path_safe,QUARANTINE)
                        #                         os.system('mv -f '+full_path_safe+' '+whichquarantinedir(safe_basename,archive=other_archive))
                        quarantine_ticket(full_path_safe, other_archive)
                        doom_flag = QUARANTINED
                    else:
                        logging.debug("untar seemed to work")

                        if safe_basename[0:2] == "S1":
                            if EXTENSION_SAFE not in unziped_safe:
                                unziped_safe += EXTENSION_SAFE
                        doom_flag = finalize_archiving(
                            archive_dir,
                            unziped_safe,
                            final_place,
                            ".tar",
                            archive_name=other_archive,
                        )
                elif full_path_safe.endswith(".zip"):
                    spool_dir = which_spool_dir(
                        safe_basename, archive=other_archive
                    )
                    logging.debug("spool dir: %s", spool_dir)
                    logging.debug("pwd: %s %s", os.curdir, os.getcwd())
                    os.chdir(spool_dir)
                    cmd = "unzip -o " + full_path_safe
                    logging.debug("command: %s", cmd)

                    try:
                        st = subprocess.check_output(
                            cmd,
                            shell=True,
                            stderr=subprocess.STDOUT,
                            text=True,
                        )
                    except subprocess.CalledProcessError as e:
                        st = e.returncode
                        logging.error(f"Error with cmd : {e}")
                        logging.error(f"status returned : {e.returncode}")
                        logging.error(f"cmd output : {e.output}")
                    logging.debug("status unzip : %s", st)
                    unziped_safe = full_path_safe.strip(".zip")
                    unziped_safe = unziped_safe.replace(
                        os.path.dirname(full_path_safe), spool_dir
                    )
                    if safe_basename[0:2] == "S1":
                        if EXTENSION_SAFE not in unziped_safe:
                            unziped_safe += EXTENSION_SAFE
                    logging.debug(
                        "unziped_safe: %s exist=%s",
                        unziped_safe,
                        os.path.exists(unziped_safe),
                    )
                    testexistenceuncompressedsafe = os.path.exists(
                        unziped_safe
                    )
                    if testexistenceuncompressedsafe:
                        doom_flag = finalize_archiving(
                            archive_dir,
                            unziped_safe,
                            final_place,
                            ".zip",
                            archive_name=other_archive,
                        )
                    else:
                        logging.error(
                            "uncompress operation on %s failed ",
                            full_path_safe,
                        )
                        # in this case the tar is kept because we are not sure that the tar itself is broken => risk of stagging tar ??
                        #                         raise Exception('fail to uncompress %s so it will be removed from spool',full_path_safe)
                        logging.error("traceback %s", traceback.format_exc())
                        #                         os.remove(full_path_safe)
                        #                         shutil.move(full_path_safe,QUARANTINE)
                        quarantine_ticket(full_path_safe, other_archive)
                        #                         os.system('mv -f '+full_path_safe+' '+whichquarantinedir(safe_basename,archive=other_archive))
                        doom_flag = QUARANTINED

                elif full_path_safe[-4:] in ["SAFE", "SEN3"]:
                    unziped_safe = full_path_safe
                    doom_flag = finalize_archiving(
                        archive_dir,
                        unziped_safe,
                        final_place,
                        archive_name=other_archive,
                    )
                elif "tar." in full_path_safe:
                    logging.debug(
                        "sentinel1_pieuvre | remove %s downloaded multiple time in spool",
                        full_path_safe,
                    )
                    #                     shutil.move(full_path_safe,QUARANTINE)
                    #                     os.system('mv -f '+full_path_safe+' '+whichquarantinedir(safe_basename))
                    quarantine_ticket(full_path_safe, other_archive)
                    doom_flag = QUARANTINED
                else:
                    logging.error(
                        "sentinel1_pieuvre | the input : %s is not conventional",
                        full_path_safe,
                    )
                #                 if level != '2' and mode != 'WV':
                if (
                    safe_basename[0:2] == "S1" and doom_flag == NORMAL
                ):  # specific behavior for sentinel-1 data
                    # march 2018, decision to remove duplicate also for WV since it gives us issues in the indexes and statistics of processing
                    cpt_dupli = check_duplicate(final_place, other_archive)
            else:
                doom_flag = TOORECENT
                logging.debug(
                    "sentinel1_pieuvre | %s has been download too recently (it will be treated at next cron execution)",
                    full_path_safe,
                )
        else:
            doom_flag = ALREADY
            # then I have to remove the SAFE from spool dir
            if dryrun is False and os.path.exists(full_path_safe):
                remove_safe_from_disk(full_path_safe)
    else:
        logging.debug(
            "sentinel1_pieuvre | %s doesnt exist anymore", full_path_safe
        )
        doom_flag = UNEXISTANT
    if doom_flag == NORMAL:
        logging.info(
            "final path where the product is stored : %s", final_place
        )
    logging.debug("final flag: %s", doom_flag)
    logging.info("final path where the product is stored : %s", final_place)
    return doom_flag, cpt_dupli


def main():
    import argparse

    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    parser = argparse.ArgumentParser(description="sort SAFE @ Ifr")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument(
        # "-i",
        "--input-safe",
        action="store",
        dest="safe",
        help="full path of a unique SAFE product to be sorted and stored",
    )
    parser.add_argument(
        "--archivename",
        choices=["datawork", "scale"],
        help="name of the archive to use datawork or scale",
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        default=False,
        help="do not unzip nor move product,"
        " to be used to check final path expected",
    )
    args = parser.parse_args()
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

    user_run = getpass.getuser()
    t0 = time.time()
    if user_run != "satwave":
        logging.warning('you must run this script with user "satwave".')
    logging.info("user : %s", user_run)
    # archive_output = ["datawork"]
    archive_output = [args.archivename]
    logging.info("the script will sort sentinel1 product : %s", args.safe)
    sort_one_safe(
        args.safe,
        other_archive=archive_output[0],
        security_second=0,
        dryrun=args.dryrun,
    )
    logging.info("time to sort the data %1.1f seconds", time.time() - t0)


if __name__ == "__main__":
    main()
