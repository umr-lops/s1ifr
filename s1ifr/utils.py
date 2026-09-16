import logging
import os

import yaml

import s1ifr


def load_config(config_path=None):
    """

    Args:
        config_path (str): path of the config file .yml [optional, default
            is localconfig.yml with fallback on config.yml]

    Returns:
        conf: dict
    """
    if config_path is None:
        local_config_path = os.path.join(
            os.path.dirname(s1ifr.__file__), "localconfig.yml"
        )

        if os.path.exists(local_config_path):
            config_path = local_config_path
        else:
            config_path = os.path.join(os.path.dirname(s1ifr.__file__), "config.yml")

    logging.debug("config path: %s", config_path)
    stream = open(config_path)
    conf = yaml.load(stream, Loader=yaml.CLoader)
    return conf


def give_me_level_from_type(type_format: str) -> str:
    """
    Determines the product level based on its type format.
    This logic now lives in the application code.
    """
    if "RAW" in type_format:
        return "L0"
    elif "OCN" in type_format:
        return "L2"
    else:
        return "L1"


def dir_data(satellite_acronym: str, config_path=None) -> str:
    """
    Constructs the ESA data path for a given satellite.
    This function now uses the loaded configuration.
    """
    config = load_config(config_path=config_path)
    # Access satellite and path info from the config dictionary
    sat_long_name = config["satellites"]["longnames"][satellite_acronym]
    datarmor_esa_archive = config["paths"]["datarmor"]["archive_esa"]

    return os.path.join(datarmor_esa_archive, sat_long_name)
