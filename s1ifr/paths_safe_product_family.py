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


def get_output_l1b_safe(slc_iw_path_safe, outputdir, productid) -> str:
    """

    this method will give the expected L1B XSP SAFE path (whatever the input SLC SAFE given as input exists or not).
    copy pasted from xsarslc processor.

    :param slc_iw_path_safe:
    :param outputdir:
    :param productid:
    :return:
        safe_output: str path of the L1B XSP SAFE
    """
    safe_basename = os.path.basename(slc_iw_path_safe)
    safestartdate = datetime.datetime.strptime(
        safe_basename.split("_")[5], "%Y%m%dT%H%M%S"
    )
    logging.debug("safe_basename : %s", safe_basename)
    safe_basename = safe_basename.replace("SLC", "XSP")
    safe_basename = safe_basename.replace(
        ".SAFE", "_" + productid.upper() + ".SAFE"
    )
    safe_output = os.path.join(
        outputdir,
        safestartdate.strftime("%Y"),
        safestartdate.strftime("%j"),
        safe_basename,
    )
    return safe_output


def add_L1B(df, cpt=None, versions=None, disable_tqdm=False, config_path=None):
    """

    collect Level-1B paths from Ifr archive.
    Multiple version/directories can be tested.

    Args:
        df (pd.DataFrame):
        cpt (collections.defaultdict(int)): [optional]
        versions (list): [optional]
        config_path (str): full path of config file .yml for s1ifr [optional]

    Return:
        df (pd.DataFrame): updated
        cpt (collections.defaultdict(int)): updated
    """
    conf = load_config(config_path=config_path)
    dir_outs_l1b = conf["paths"]["datawork"]["dir_outs_l1b"]
    DEFAULT_VERSIONS_L1B = conf["DEFAULT_VERSIONS_L1B"]
    if versions is None:
        versions = DEFAULT_VERSIONS_L1B
    logging.info("Level-1B version to be tested: %s", versions)
    if cpt is None:
        cpt = defaultdict(int)

    L1B_found = {}
    # loop over all SLC SAFE
    for xx in tqdm(range(len(df["L1_SLC"])), disable=disable_tqdm):
        ii = df["L1_SLC"].iloc[xx]
        assert isinstance(ii, str)
        # get full path of SLC SAFE
        if "/" not in ii:

            fp = s1ifr.get_path_from_base_safe.get_path_from_base_safe(
                ii, archive_name="datawork"
            )
            if not os.path.exists(fp):
                fp = s1ifr.get_path_from_base_safe.get_path_from_base_safe(
                    ii, archive_name="scale"
                )
        else:
            fp = ii
        found = False
        cpt["total_safe_slc"] += 1
        if fp != "" and fp is not None and os.path.exists(fp):
            cpt["total_safe_slc_avail_at_ifr"] += 1
            # loop over versions of L1B XSP
            for pid in versions:  # ,'A15'
                found_version = False
                # loop over output directories for a given version
                for out in dir_outs_l1b:
                    if pid not in L1B_found:
                        L1B_found[pid] = []
                    safel1b = get_output_l1b_safe(
                        fp, outputdir=out, productid=pid
                    )
                    if os.path.exists(safel1b):
                        cpt["L1B_" + pid + "_found"] += 1
                        # path_l1b[versionl1b_complete].append(safel1b)
                        found = True
                        found_version = True
                        break  # break loop on directories
                    else:
                        pass
                if found_version is True:
                    # logging.debug('break loop')

                    L1B_found[pid].append(safel1b)
                else:
                    cpt["L1B_" + pid + "_absent"] += 1
                    L1B_found[pid].append("")

        else:
            cpt["SLC_absent"] += 1
        if found is True:
            cpt["L1B_found"] += 1
            # L1B_found.append(safel1b)
        else:
            # L1B_found.append('')
            cpt["L1B_absent"] += 1

    L1B_found = pd.DataFrame(L1B_found)
    for uu in L1B_found:
        sumnotnull = (L1B_found[uu] != "").sum()
        pct = (
            sumnotnull / cpt["total_safe_slc"] * 100
            if cpt["total_safe_slc"] > 0
            else 0
        )
        logging.info(
            "version: %s -> %i safe found (%.1f%%)", uu, sumnotnull, pct
        )
        df[f"L1B_XSP_{uu}"] = L1B_found[uu]
    # df['L1B_XSP'] = L1B_found[versions[-1]]
    logging.info("counter: %s", cpt)
    return df, cpt


def add_L1C(
    df, versions=None, cpt=None, disable_tqdm=False, config_path=None
) -> pd.DataFrame:
    """
    from L1B path I want easily find L1C

    Args:
        df (pd.DataFrame):
        cpt (collection.defaultdict(int)): [optional]
        disable_tqdm (bool): True -> no progress bar [optional]
        config_path (str): full path of config file .yml for s1ifr [optional]
    """
    conf = load_config(config_path=config_path)
    DEFAULT_VERSIONS_L1C = conf["DEFAULT_VERSIONS_L1C"]
    dir_outs_l1c = conf["paths"]["datawork"]["dir_outs_l1c"]
    if versions is None:
        versions = DEFAULT_VERSIONS_L1C
    logging.info("Level-1C will be search in versions: %s", versions)
    path_l1c = {}
    if cpt is None:
        cpt = defaultdict(int)
    for xx in tqdm(range(df.index.size), disable=disable_tqdm):
        # pbar.set_description('l1c: %s'%cpt)
        l1c_found = False
        ii = df["L1_SLC"].iloc[xx]
        if "/" not in ii:
            fp = s1ifr.get_path_from_base_safe.get_path_from_base_safe(
                ii, archive_name="datawork"
            )
            if not os.path.exists(fp):
                fp = s1ifr.get_path_from_base_safe.get_path_from_base_safe(
                    ii, archive_name="scale"
                )
        else:
            fp = ii
        for versionl1c in versions:
            l1c_found_version_span = False
            versionl1c_complete = "L1C_XSP_" + versionl1c
            if versionl1c_complete not in path_l1c:
                path_l1c[versionl1c_complete] = []
            for out in dir_outs_l1c:
                # valuepathl1c = get_output_l1b_filepath(
                #    fp + ":IW1", outputdir=out, productid=versionl1c
                # )
                safel1c = get_output_l1b_safe(
                    fp, outputdir=out, productid=versionl1c
                )

                if os.path.exists(safel1c):
                    cpt["L1C_" + versionl1c + "_found"] += 1
                    path_l1c[versionl1c_complete].append(safel1c)
                    l1c_found = True
                    l1c_found_version_span = True
                    break  # break loop on directories
                else:
                    pass
            if (
                l1c_found_version_span is False
            ):  # all L1B version browsed and no match
                cpt["L1C_" + versionl1c + "_absent"] += 1
                path_l1c[versionl1c_complete].append("")
        logging.debug("all L1C versions tested")

        if (
            l1c_found is False
        ):  # all L1B versions and all L1C version browsed and no match
            cpt["L1C_absent"] += 1
        else:
            cpt["L1C_found"] += 1
    logging.info("cpt : %s", cpt)
    for uu in path_l1c:
        logging.info("append column L1C %s to the dataframe", uu)
        df[uu] = path_l1c[uu]
    return df, cpt


def add_L2WAV(
    df, versions=None, cpt=None, disable_tqdm=False, config_path=None
) -> pd.DataFrame:
    """
    from SLC path I want easily find L2-WAV

    Args:
        df (pd.DataFrame):
        cpt (collection.defaultdict(int)): [optional]
        disable_tqdm (bool): [default False -> no progress bar in stdout]
        config_path (str): full path of config file .yml for s1ifr [optional]
    """
    conf = load_config(config_path=config_path)
    dir_out_l2wav = conf["paths"]["datawork"]["dir_out_l2wav"]
    DEFAULT_VERSIONS_L2WAV = conf["DEFAULT_VERSIONS_L2WAV"]
    if versions is None:
        versions = DEFAULT_VERSIONS_L2WAV
    logging.info("Level-2 WAV will be search in versions: %s", versions)
    path_l2w = {}
    if cpt is None:
        cpt = defaultdict(int)
    for xx in tqdm(range(df.index.size), disable=disable_tqdm):
        # pbar.set_description('l1c: %s'%cpt)
        l2_found = False
        ii = df["L1_SLC"].iloc[xx]
        if "/" not in ii:
            fp = s1ifr.get_path_from_base_safe.get_path_from_base_safe(
                ii, archive_name="datawork"
            )
            if not os.path.exists(fp):
                fp = s1ifr.get_path_from_base_safe.get_path_from_base_safe(
                    ii, archive_name="scale"
                )
        else:
            fp = ii
        for versionl2 in versions:
            l2_found_version_span = False
            versionl2_complete = "L2_WAV_" + versionl2
            if versionl2_complete not in path_l2w:
                path_l2w[versionl2_complete] = []
            for out in dir_out_l2wav:
                # valuepathl1c = get_output_l1b_filepath(ii + ':IW1', outputdir=out, productid=versionl2)
                base_safe = os.path.basename(fp)
                # print('base_safe',base_safe,ii,os.path.basename(ii).split('_')[5])
                datedt__slc = datetime.datetime.strptime(
                    base_safe.split("_")[5], "%Y%m%dT%H%M%S"
                )
                base_safe_l2 = (
                    base_safe.replace("SLC", "WAV")
                    .replace("_1S", "_2S")
                    .replace(".SAFE", "_" + versionl2 + ".SAFE")
                )
                valuepathl2wav = os.path.join(
                    out,
                    datedt__slc.strftime("%Y"),
                    datedt__slc.strftime("%j"),
                    base_safe_l2,
                )
                if os.path.exists(valuepathl2wav):
                    cpt["L2_WAV_" + versionl2 + "_found"] += 1
                    path_l2w[versionl2_complete].append(valuepathl2wav)
                    l2_found = True
                    l2_found_version_span = True
                    break  # break loop on directories
                else:
                    pass
            if (
                l2_found_version_span is False
            ):  # all L1B version browsed and no match
                cpt["L2_WAV_" + versionl2 + "_absent"] += 1
                path_l2w[versionl2_complete].append("")
        logging.debug("all L2WAV versions tested")

        if (
            l2_found is False
        ):  # all L1B versions and all L1C version browsed and no match
            cpt["L2WAV_absent"] += 1
        else:
            cpt["L2WAV_found"] += 1
    logging.info("cpt : %s", cpt)
    for uu in path_l2w:
        logging.info("append column L2-WAV %s to the dataframe", uu)
        df[uu] = path_l2w[uu]
    return df, cpt


def add_SLC(df, cpt=None):
    """

    to be used if the input listing is GRD

    Args:
        df (pd.DataFrame):
        cpt (collections.defaultditc(int)): [optional]
    :return:
    """
    if cpt is None:
        cpt = defaultdict(int)
    GRD_withou_SLC = []
    SLC = []
    for uu in df["grd"]:
        slc = match_slc_grd(uu, type_input="GRDH", type_seek="SLC_")
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
    df, l1bversions=None, l1cversions=None, disable_tqdm=False
) -> pd.DataFrame:
    """
    wrapper method to add Level-1B , Level-1C and Level-2 WAV paths associated to initial SAFE

    Args:
        df: pandas.DataFrame with 'L1_SLC' column filled with SAFE paths
        l1bversions: list of str ['A12'] for instance [optional]
        l1cversions : list of str ['B17'] for instance [optional]
        disable_tqdm: bool
    Returns:
        df: pandas.DataFrame with new columns

    """
    cpt = defaultdict(int)
    if "L1_SLC" not in df:
        df, cpt = add_SLC(df, cpt=cpt)
    df, cpt = add_L1B(
        df, cpt=cpt, versions=l1bversions, disable_tqdm=disable_tqdm
    )
    df, cpt = add_L1C(
        df, cpt=cpt, versions=l1cversions, disable_tqdm=disable_tqdm
    )
    df, cpt = add_L2WAV(df, versions=None, cpt=cpt, disable_tqdm=disable_tqdm)
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


if __name__ == "__main__":
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
    args = parser.parse_args()
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
    newdf = get_products_family(
        merged_df, l1bversions=args.l1bversions, l1cversions=args.l1cversions
    )
    fout = os.path.join(
        args.outputdir,
        "product_family_{}.csv".format(
            os.path.basename(args.listing).replace(".txt", "")
        ),
    )
    # drop empty columns:
    newdf = newdf.loc[:, (newdf != "").any()]
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
