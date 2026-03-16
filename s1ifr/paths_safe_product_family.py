"""
methods to get dataframe from SLC L1 to L1B and L1C and L2
in order to check the completness of a given listing
Janaury 2025
"""

import datetime
import logging
import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from tqdm import tqdm

import s1ifr
from s1ifr.match_SLC_GRD import match_slc_grd
from s1ifr.utils import load_config

# --- SHARED HELPER METHODS ---


def _resolve_slc_path(slc_identifier):
    """
    Resolves the physical path of an SLC SAFE from various archives.

    Args:
        slc_identifier (str): Filename or full path of the SLC SAFE.

    Returns:
        str or None: Full path if found, else None.
    """
    if "/" in slc_identifier:
        return slc_identifier if os.path.exists(slc_identifier) else None

    # Try datawork archive
    fp = s1ifr.get_path_from_base_safe.get_path_from_base_safe(
        slc_identifier, archive_name="datawork"
    )
    if os.path.exists(fp):
        return fp

    # Fallback to scale archive
    fp = s1ifr.get_path_from_base_safe.get_path_from_base_safe(
        slc_identifier, archive_name="scale"
    )
    return fp if os.path.exists(fp) else None


def get_output_l1b_safe(slc_iw_path_safe, outputdir, productid) -> str:
    """
    Predicts the expected L1B/L1C XSP SAFE path based on an SLC path.

    Args:
        slc_iw_path_safe (str): Path to source SLC.
        outputdir (str): Base output directory.
        productid (str): Version/Product ID (e.g., 'A14').

    Returns:
        str: Constructured path.
    """
    safe_basename = os.path.basename(slc_iw_path_safe)
    safestartdate = datetime.datetime.strptime(
        safe_basename.split("_")[5], "%Y%m%dT%H%M%S"
    )
    safe_basename = safe_basename.replace("SLC", "XSP")
    safe_basename = safe_basename.replace(
        ".SAFE", "_" + productid.upper() + ".SAFE"
    )
    return os.path.join(
        outputdir,
        safestartdate.strftime("%Y"),
        safestartdate.strftime("%j"),
        safe_basename,
    )


def get_output_l2wav_safe(slc_path, outputdir, productid) -> str:
    """
    Predicts the expected L2 WAV SAFE path based on an SLC path.

    Args:
        slc_path (str): Path to source SLC.
        outputdir (str): Base output directory.
        productid (str): Version/Product ID.

    Returns:
        str: Constructed path.
    """
    base_safe = os.path.basename(slc_path)
    datedt_slc = datetime.datetime.strptime(
        base_safe.split("_")[5], "%Y%m%dT%H%M%S"
    )
    base_safe_l2 = (
        base_safe.replace("SLC", "WAV")
        .replace("_1S", "_2S")
        .replace(".SAFE", "_" + productid + ".SAFE")
    )
    return os.path.join(
        outputdir,
        datedt_slc.strftime("%Y"),
        datedt_slc.strftime("%j"),
        base_safe_l2,
    )


def _find_version_path(slc_path, pid, search_dirs, path_generator_func):
    """Generic helper to find a versioned product across multiple directories."""
    for out_dir in search_dirs:
        candidate = path_generator_func(slc_path, out_dir, pid)
        if os.path.exists(candidate):
            return candidate
    return None


# --- L1B SPECIFIC LOGIC ---


def _process_l1b_row(slc_id, versions, dir_outs, cpt):
    row_results = {pid: "" for pid in versions}
    cpt["total_safe_slc"] += 1
    fp = _resolve_slc_path(slc_id)

    if not fp:
        cpt["SLC_absent"] += 1
        cpt["L1B_absent"] += 1
        return row_results

    cpt["total_safe_slc_avail_at_ifr"] += 1
    found_any = False
    for pid in versions:
        res = _find_version_path(fp, pid, dir_outs, get_output_l1b_safe)
        if res:
            row_results[pid] = res
            cpt[f"L1B_{pid}_found"] += 1
            found_any = True
        else:
            cpt[f"L1B_{pid}_absent"] += 1

    cpt["L1B_found" if found_any else "L1B_absent"] += 1
    return row_results


def add_L1B(df, cpt=None, versions=None, disable_tqdm=False, config_path=None):
    """
    Collect Level-1B paths from Ifr archive.

    Args:
        df (pd.DataFrame): Input dataframe with 'L1_SLC' column.
        cpt (defaultdict): Counters dictionary.
        versions (list): List of versions to search.
        disable_tqdm (bool): Disable progress bar.
        config_path (str): Path to config file.

    Returns:
        tuple: (updated df, updated cpt)
    """
    conf = load_config(config_path=config_path)
    dir_outs = conf["paths"]["datawork"]["dir_outs_l1b"]
    versions = versions or conf["DEFAULT_VERSIONS_L1B"]
    cpt = cpt if cpt is not None else defaultdict(int)

    logging.info("Level-1B version to be tested: %s", versions)
    results = [
        _process_l1b_row(sid, versions, dir_outs, cpt)
        for sid in tqdm(df["L1_SLC"], disable=disable_tqdm)
    ]

    res_df = pd.DataFrame(results)
    for pid in versions:
        df[f"L1B_XSP_{pid}"] = res_df[pid].values
        logging.info(
            "version: %s -> %i safe found", pid, (res_df[pid] != "").sum()
        )

    return df, cpt


# --- L1C SPECIFIC LOGIC ---


def _process_l1c_row(slc_id, versions, dir_outs, cpt):
    row_results = {f"L1C_XSP_{pid}": "" for pid in versions}
    fp = _resolve_slc_path(slc_id)
    if not fp:
        cpt["L1C_absent"] += 1
        return row_results

    found_any = False
    for pid in versions:
        res = _find_version_path(fp, pid, dir_outs, get_output_l1b_safe)
        if res:
            row_results[f"L1C_XSP_{pid}"] = res
            cpt[f"L1C_{pid}_found"] += 1
            found_any = True
        else:
            cpt[f"L1C_{pid}_absent"] += 1

    cpt["L1C_found" if found_any else "L1C_absent"] += 1
    return row_results


def add_L1C(df, versions=None, cpt=None, disable_tqdm=False, config_path=None):
    """
    From L1 path, find associated L1C XSP products.

    Args:
        df (pd.DataFrame): Input dataframe.
        versions (list): L1C versions.
        cpt (defaultdict): Counters.
        disable_tqdm (bool): Progress bar control.
        config_path (str): Config file path.

    Returns:
        tuple: (updated df, updated cpt)
    """
    conf = load_config(config_path=config_path)
    dir_outs = conf["paths"]["datawork"]["dir_outs_l1c"]
    versions = versions or conf["DEFAULT_VERSIONS_L1C"]
    cpt = cpt if cpt is not None else defaultdict(int)

    logging.info("Level-1C version to be tested: %s", versions)
    results = [
        _process_l1c_row(sid, versions, dir_outs, cpt)
        for sid in tqdm(df["L1_SLC"], disable=disable_tqdm)
    ]

    res_df = pd.DataFrame(results)
    for col in res_df.columns:
        df[col] = res_df[col].values

    logging.info("cpt : %s", cpt)
    return df, cpt


# --- L2WAV SPECIFIC LOGIC ---


def _process_l2wav_row(slc_id, versions, dir_outs, cpt):
    row_results = {f"L2_WAV_{pid}": "" for pid in versions}
    fp = _resolve_slc_path(slc_id)
    if not fp:
        cpt["L2WAV_absent"] += 1
        return row_results

    found_any = False
    for pid in versions:
        res = _find_version_path(fp, pid, dir_outs, get_output_l2wav_safe)
        if res:
            row_results[f"L2_WAV_{pid}"] = res
            cpt[f"L2_WAV_{pid}_found"] += 1
            found_any = True
        else:
            cpt[f"L2_WAV_{pid}_absent"] += 1

    cpt["L2WAV_found" if found_any else "L2WAV_absent"] += 1
    return row_results


def add_L2WAV(
    df, versions=None, cpt=None, disable_tqdm=False, config_path=None
):
    """
    From SLC path, find associated L2-WAV products.

    Args:
        df (pd.DataFrame): Input dataframe.
        versions (list): L2 versions.
        cpt (defaultdict): Counters.
        disable_tqdm (bool): Progress bar control.
        config_path (str): Config file path.

    Returns:
        tuple: (updated df, updated cpt)
    """
    conf = load_config(config_path=config_path)
    dir_outs = conf["paths"]["datawork"]["dir_out_l2wav"]
    versions = versions or conf["DEFAULT_VERSIONS_L2WAV"]
    cpt = cpt if cpt is not None else defaultdict(int)

    logging.info("Level-2 WAV version to be tested: %s", versions)
    results = [
        _process_l2wav_row(sid, versions, dir_outs, cpt)
        for sid in tqdm(df["L1_SLC"], disable=disable_tqdm)
    ]

    res_df = pd.DataFrame(results)
    for col in res_df.columns:
        df[col] = res_df[col].values

    logging.info("cpt : %s", cpt)
    return df, cpt


def add_SLC(df, cpt=None, config_path=None):
    """

    to be used if the input listing is GRD

    Args:
        df (pd.DataFrame):
        cpt (collections.defaultditc(int)): [optional]
        config_path (str): [optional]
    :return:
    """
    if cpt is None:
        cpt = defaultdict(int)
    GRD_withou_SLC = []
    SLC = []
    for uu in df["grd"]:
        slc = match_slc_grd(uu, type_input="GRDH", type_seek="SLC_",
                             config_path=config_path)
        if slc is None:
            cpt["SLC_absent"] += 1
            GRD_withou_SLC.append(uu)
            SLC.append("")
        else:
            cpt["SLC_found"] += 1
            SLC.append(slc)
    df["L1_SLC"] = SLC
    logging.info(cpt)
    for uu in GRD_withou_SLC:
        logging.info("missing SLC for GRD %s", uu)
    return df, cpt


def get_products_family(
    df, l1bversions=None, l1cversions=None, disable_tqdm=False, config=None
) -> pd.DataFrame:
    """
    wrapper method to add Level-1B , Level-1C and Level-2 WAV paths associated to initial SAFE

    Args:
        df: pandas.DataFrame with 'L1_SLC' column filled with SAFE paths
        l1bversions: list of str ['A12'] for instance [optional]
        l1cversions : list of str ['B17'] for instance [optional]
        disable_tqdm: bool
        config: str path of the config [optional default=None]
    Returns:
        df: pandas.DataFrame with new columns

    """
    cpt = defaultdict(int)
    if "L1_SLC" not in df:
        df, cpt = add_SLC(df, cpt=cpt, config_path=config)
    df, cpt = add_L1B(
        df, cpt=cpt, versions=l1bversions, disable_tqdm=disable_tqdm,
          config_path=config
    )
    df, cpt = add_L1C(
        df, cpt=cpt, versions=l1cversions, disable_tqdm=disable_tqdm, 
        config_path=config
    )
    df, cpt = add_L2WAV(df, versions=None, cpt=cpt, disable_tqdm=disable_tqdm,
                        config_path=config)
    logging.info("\n=====================================\n")
    for kee in sorted([kk for kk in cpt]):
        if bool(re.search(r"\d{2}", kee)):
            indent = "\t"
        else:
            indent = ""
        logging.info("%s%s: %s", indent, kee, cpt[kee])
    logging.info("\n=====================================\n")
    return df


def create_a_listing(newdf):
    try:
        # 1. Ask for the column name
        consign = f"Enter the column name to filter: possibles names are : {newdf.keys()}"
        input_from_user_colname = input(consign).strip()

        # (Optional) Validate that column exists to prevent a crash later
        if input_from_user_colname not in newdf.columns:
            print(
                f"Error: Column '{input_from_user_colname}' does not exist in the DataFrame."
            )
            sys.exit(1)

        # 2. Ask for the output path
        output_listing_sub_product_path = input(
            "Enter the full path for the output CSV: "
        ).strip()

        # --- Your Logic ---
        serii = newdf[input_from_user_colname].where(
            newdf[input_from_user_colname].str.strip() != "", np.nan
        )

        # Save to CSV
        serii.dropna().to_csv(
            output_listing_sub_product_path, header=False, index=False
        )

        logging.info("output = %s", output_listing_sub_product_path)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        logging.error("An error occurred: %s", e)


def entrypoint():
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    import argparse

    parser = argparse.ArgumentParser(description="productfamily")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument(
        "--listing",
        action="store",
        required=True,
        help="input listing with SAFE SLC",
    )
    parser.add_argument(
        "--outputdir",
        help="folder where the data will be written [optional]",
        required=False,
        default=".",
    )
    parser.add_argument(
        "--l1bversions",
        nargs="+",
        help="Provide one or more L1B versions A14 A15 A16 ...",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--l1cversions",
        nargs="+",
        help="Provide one or more L1C versions B17 B18 ...",
        required=False,
        default=None,
    )
    parser.add_argument(
        '--config',
        help='path of s1ifr config.yml file [optional default=None]',
        required=False,
        default=None
    )
    args = parser.parse_args()
    assert os.path.isdir(args.outputdir)
    fmt = "%(asctime)s %(levelname)s %(filename)s(%(lineno)d) %(message)s"
    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG, format=fmt, datefmt="%d/%m/%Y %H:%M:%S"
        )
    else:
        logging.basicConfig(
            level=logging.INFO, format=fmt, datefmt="%d/%m/%Y %H:%M:%S"
        )
    merged_df = pd.read_csv(args.listing, names=["L1_SLC"])
    logging.debug("L1B versions %s", args.l1bversions)
    logging.debug("L1C versions %s", args.l1cversions)
    logging.debug('config path: %s',args.config)
    newdf = get_products_family(
        merged_df, l1bversions=args.l1bversions, l1cversions=args.l1cversions,
        config=args.config
    )
    fout = os.path.join(
        args.outputdir,
        "product_family_{}.csv".format(
            os.path.basename(args.listing).replace(".txt", "")
        ),
    )
    # drop empty columns:
    newdf = newdf.loc[:, (newdf != "").any()]
    breakpoint()
    newdf.to_csv(fout, header=True, index=True)

    logging.info("output file: %s", fout)
    logging.info("possible families to put into a listing: %s", newdf.keys())
    # add a ligne to let the user selct the good column of the dataframe
    create_a_listing(newdf)
    # input_from_user_colname = ...
    # serii = newdf[input_from_user_colname].where(newdf[input_from_user_colname].str.strip() != '', np.nan)
    # output_listing_sub_product_path = ....
    # serii.dropna().to_csv(output_listing_sub_product_path,header=False,index=False)
    # logging.info('output = %s',output_listing_sub_product_path)
    # print(
    #     "example of command to execute \n serii = newdf['L1B_XSP_A23'].where(newdf['L1B_XSP_A23'].str.strip() != '', np.nan) \n serii.dropna().to_csv('/home/datawork-cersat-public/project/sarwave/data/listings/swot_colocated_IW_L1B_XSP_A23_safe_sentinel1_present_at_ifremer_2025-08-28_sdv_only.csv',header=False,index=False) "
    # )
    # import pdb

    # pdb.set_trace()
    # # print(newdf)


if __name__ == "__main__":
    entrypoint()
