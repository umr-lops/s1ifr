import os

macro_MODES = ["SM", "WV", "IW", "EW"]
PROJECT_DIR_DATARMOR = (
    "/home/datawork-cersat-public/cache/project/mpc-sentinel1/"
)
PROJECT_DIR_DATARMOR_ALT = (
    "/home/datawork-cersat-public/project/mpc-sentinel1/"
)
datarmor_archive_esa_ifremer = os.path.join(
    PROJECT_DIR_DATARMOR_ALT, "data", "esa"
)
WORKBENCH_SCALE = "/scale/project/lops-siam-sentinel1-workbench/"
scale_archive_esa_ifremer = os.path.join(WORKBENCH_SCALE, "data", "esa")
dir_suspect = "/home1/scratch/satwave"
dirdeleted = "/home1/scratch/satwave"

EXTENSIONS = {"L1": "tiff", "L2": "nc"}


def give_me_level_from_type(type_format):
    """
    type_format (str): ex: GRDH
    """
    if "RAW" in type_format:
        level = "L0"
    elif "OCN" in type_format:
        level = "L2"
    else:
        level = "L1"
    return level


TYPES = ["OCN_", "GRDH", "SLC_", "GRDM", "GRDF", "RAW_"]
sats_acro = {
    "S1A": "sentinel-1a",
    "S1B": "sentinel-1b",
    "S1C": "sentinel-1c",
    "S1D": "sentinel-1d",
}
sats_full = {
    "sentinel-1a": "S1A",
    "sentinel-1b": "S1B",
    "sentinel-1c": "S1C",
    "sentinel-1d": "S1D",
}


def dir_data(satellite):
    satlong = sats_acro[satellite]
    return os.path.join(PROJECT_DIR_DATARMOR, "data", "esa", satlong)


WORKING_DIR = os.path.join(PROJECT_DIR_DATARMOR_ALT, "workspace")
WORKING_DIR_SCALE = WORKBENCH_SCALE

QUARANTINE = {
    "datarmor_mpc": os.path.join(
        PROJECT_DIR_DATARMOR, "workspace", "quarantine/"
    )
}
DIR_SATWWAVE_SCRATCH = "/home1/scratch/satwave/"
