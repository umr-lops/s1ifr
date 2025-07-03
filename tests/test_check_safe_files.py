import logging
import os
import shutil
import time
from xml.dom import minidom
import datetime
from s1ifr import utils

# This assumes 'conf' is loaded at the module level
conf = utils.load_config()

# ... (other functions like delete_corrupted_safe, etc.) ...

def check_number_of_measurment(manifestpath: str) -> bool:
    """
    Checks if all measurement files listed in the manifest exist on disk.

    Args:
        manifestpath: The full path to the manifest.safe file.

    Returns:
        True if all files exist, False otherwise or if the manifest is unreadable.
    """
    basedir = os.path.dirname(manifestpath)
    nb_meas = 0
    nb_ok = 0

    # REASON FOR CHANGE:
    # Wrap the parsing in a try...except block to gracefully handle
    # corrupted or unreadable XML files. This makes the function more robust.
    try:
        xmlcontent = minidom.parse(manifestpath)
        file_locations = xmlcontent.getElementsByTagName('fileLocation')
        for file_location in file_locations:
            if 'measurement' in file_location.getAttribute('href'):
                nb_meas += 1
                file_to_check = os.path.join(basedir, file_location.getAttribute('href'))
                if os.path.exists(file_to_check):
                    nb_ok += 1
    except Exception as e:
        # If any error occurs during parsing, log it and treat it as a failure.
        logging.error("Failed to parse manifest '%s': %s", manifestpath, e)
        return False

    if nb_meas == nb_ok and nb_meas > 0:
        return True
    else:
        logging.warning('%s/%s measurement files are present in %s', nb_ok, nb_meas, basedir)
        return False

# ... (the rest of your functions like safe_checker, etc.) ...

# Make sure to include the other functions from your original file here.
# The following are placeholders for completeness.

def write_to_log(logpath, reason, safe):
    # implementation
    pass

def check_presence_of_manifest_file(safe_path):
    # implementation
    return True

def check_sub_directories(safe_path):
    # implementation
    return True

def delete_corrupted_safe(corrupted_list, dirout):
    # implementation
    return 0

def safe_checker(safe_path, logpath):
    # implementation
    return True