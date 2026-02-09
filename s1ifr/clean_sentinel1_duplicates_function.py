"""Clean multiple occurrences of the same SAFE file in Sentinel-1 data.

This script identifies duplicate Sentinel-1 products based on their acquisition
parameters and keeps only the version with the latest processing time. 
Old versions are moved to quarantine or deleted. It is designed to be called 
by the Sentinel-1 'pieuvre' (data ventilation) system.

Example:
    ``find $PWD -maxdepth 1 -name '*SAFE' | python clean_sentinel1_duplicates_function.py --safe [SAFE_PATH]``

Attributes:
    Author: Antoine Grouazel
    Date: April 2014
"""

import collections
import datetime
import fnmatch
import logging
import os

import numpy as np
from lxml import etree

from s1ifr.quarantine_management import quarantine_ticket


def get_ending_processing_time(safe_full_path):
    """Extract the stop processing time from the SAFE manifest file.

    Args:
        safe_full_path (str): Full path to the SAFE directory.

    Returns:
        datetime.datetime: The processing stop time extracted from the manifest. 
            Returns 2014-01-01 as a default value if the manifest is missing or empty.
    """
    pattern = "/metadataObject/metadataWrap/xmlData/{http://www.esa.int/safe/sentinel-1.0}processing"
    path_manifest = os.path.join(safe_full_path, "manifest.safe")
    tmp = datetime.datetime(2014, 1, 1)  # dummy value
    if os.path.isfile(path_manifest) and os.path.getsize(path_manifest) > 0:
        tree = etree.parse(path_manifest)
        processingdates = tree.findall("./" + pattern)
        processingdates = processingdates[0]
        tmp = processingdates.attrib["stop"]
        tmp = datetime.datetime.strptime(tmp, "%Y-%m-%dT%H:%M:%S.%f")
    return tmp


def spot_dupli_core(safebasename, repdata):
    """Identify duplicate SAFE products and find the latest processed version.

    Searches for files matching the acquisition prefix of the provided basename
    within the specified directory and compares their processing dates.

    Args:
        safebasename (str): Basename of the S1 SAFE product to check.
        repdata (str): Path to the directory where potential duplicates are stored.

    Returns:
        tuple: A tuple containing:
            - int: Index of the latest processed file in the occurrence list.
            - list: Full paths of all potential occurrences found.
            - numpy.ndarray: Array of processing stop times for each occurrence.
    """
    begninig = safebasename[0:-10]
    logging.debug("begninig = %s", begninig)
    indice_latest_processing = None
    potentialoccurenceies = []
    stoptimes = None
    for root, dirnames, filenames in os.walk(repdata):
        for filename in fnmatch.filter(dirnames, begninig + "*.SAFE"):
            potentialoccurenceies.append(os.path.join(root, filename))
    if potentialoccurenceies is not None and len(potentialoccurenceies) > 1:
        indice_latest_processing, potentialoccurenceies, stoptimes = (
            latest_safe_processed(potentialoccurenceies)
        )
    return indice_latest_processing, potentialoccurenceies, stoptimes


def latest_safe_processed(duplicates_list):
    """Compare processing times for a list of duplicate SAFE products.

    Args:
        duplicates_list (list): List of full paths to duplicate SAFE products.

    Returns:
        tuple: A tuple containing:
            - int: Index of the latest processed version in the list.
            - list: The input duplicates_list.
            - numpy.ndarray: Array of processing stop times (datetime objects).
    """
    stoptimes = np.array([])
    for yy, pot in enumerate(duplicates_list):
        logging.debug("duplicate %s %s", pot, yy)
        tmp = get_ending_processing_time(pot)
        stoptimes = np.append(stoptimes, tmp)
    indice_latest_processing = np.argmax(stoptimes)
    logging.debug(
        "indice of the file with the latest processing date %s",
        indice_latest_processing,
    )
    return indice_latest_processing, duplicates_list, stoptimes


def check_duplicate(file_to_be_checked, archive="datawork", dryrun=True):
    """Detect and remove duplicate SAFEs based on processing time.

    Identifies SAFEs with the same acquisition dates as the input file. 
    Keeps only the version with the latest processing time and sends others 
    to quarantine.

    Args:
        file_to_be_checked (str): Full path of the .SAFE (or .tar) to be checked.
        archive (str): Storage name ('scale' or 'datawork'). Defaults to "datawork".
        dryrun (bool): If True, logs actions without deleting/moving files. Defaults to True.

    Returns:
        int: Number of duplicate files identified for removal.
    """
    cpt_deleted = 0
    logging.debug("test duplication of %s", file_to_be_checked)
    file_to_be_checked = file_to_be_checked.rstrip(".tar")
    tmpbase = os.path.basename(file_to_be_checked)
    repdata = os.path.dirname(file_to_be_checked)
    (
        indice_latest_processing,
        potentialoccurenceies,
        ending_processing_times,
    ) = spot_dupli_core(tmpbase, repdata)
    if potentialoccurenceies is not None and len(potentialoccurenceies) > 1:
        logging.debug(
            "%s duplicates found and will be removed",
            len(potentialoccurenceies),
        )
        for yy, pot in enumerate(potentialoccurenceies):
            if yy != indice_latest_processing:
                cpt_deleted += 1
                logging.debug("to delete %s", pot)
                if dryrun is False:
                    quarantine_ticket(pot, archive)

    else:
        logging.debug("no duplicate found")
    logging.debug("end of the sentinel duplicate check")
    return cpt_deleted


def main():
    """Main entry point for the CLI tool to clean SAFE duplicates."""
    import argparse

    parser = argparse.ArgumentParser(description="clean SAFE duplicate")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument(
        "--dryrun",
        action="store_true",
        default=False,
        help="[default = False], True -> data is not moved nor deleted",
    )
    parser.add_argument(
        "--safe", required=True, action="store", help="SAFE path to test"
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)-5s %(message)s",
            datefmt="%d/%m/%Y %H:%M:%S",
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-5s %(message)s",
            datefmt="%d/%m/%Y %H:%M:%S",
        )
    cpt = collections.defaultdict(int)
    logging.info("start the check")
    
    cpt_deleted = check_duplicate(
        file_to_be_checked=args.safe, dryrun=args.dryrun
    )
    cpt["total_safe_analysed"] += 1
    cpt["total_safe_removed"] += cpt_deleted
    
    if cpt_deleted == 0:
        cpt["total_acqui_already_ok"] += 1
    else:
        cpt["total_acqui_already_fixed"] += 1
        
    if cpt["total_safe_analysed"] % 100 == 1:
        logging.info("counter for duplicate fixing S1: %s", cpt)
    logging.info("fin script : %s", cpt)


if __name__ == "__main__":
    main()