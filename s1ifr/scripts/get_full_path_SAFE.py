#!/usr/bin/bash
"""
You have a base SAFE listing -> you get a full path SAFE listing (Ifremer archive)
"""

import argparse
import logging
from collections import defaultdict

import numpy as np
import pandas as pd
from tqdm import tqdm

from s1ifr.get_path_from_base_safe import get_path_from_base_safe


def parseargs():
    parser = argparse.ArgumentParser(description="base->full")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument(
        "--input",
        required=True,
        help="input listing (.txt or .lst or .csv) containing base SAFE or directly a single base SAFE",
    )
    parser.add_argument(
        "--check_existence",
        action="store_true",
        default=False,
        help="True -> check whether a SAFE exist on disk",
    )
    parser.add_argument(
        "--remove_empty_lines",
        action="store_true",
        default=False,
        help="True -> remove empty lines ti get clean listing.",
    )
    # parser.add_argument(
    #     "--archivename",
    #     required=False,
    #     default="datawork",
    #     help="name of the archive 'scale' or 'datawork' or ...",
    # )

    parser.add_argument(
        "--output",
        required=True,
        help="output listing containing full path SAFE",
    )
    args = parser.parse_args()
    return args


def main(verbose, input, output, check_existence, remove_empty_lines):
    """

    Treat one or many SAFE basenames to find full path in Ifr archive

    """

    fmt = "%(asctime)s %(levelname)s %(filename)s(%(lineno)d) %(message)s"
    if verbose:
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
    if input.endswith((".csv", ".txt", ".lst")):
        df = pd.read_csv(input, names=["base"])
    else:
        assert ".SAFE" in input
        logging.info("test a single SAFE")
        df = pd.DataFrame({"base": [input]})
    all_fp = []
    cpt = defaultdict(int)
    for ii in tqdm(range(len(df["base"]))):
        safe = df["base"].iloc[ii].replace(".zip", "")
        fp = get_path_from_base_safe(
            safe_basename=safe,
            archive_name="scale",
            check_existence=check_existence,
        )
        if fp is None:
            fp = get_path_from_base_safe(
                safe_basename=safe,
                archive_name="datawork",
                check_existence=check_existence,
            )
        # add a test without unique ID and glob
        if fp is not None:
            pass
            cpt["ok"] += 1
        else:
            fp = np.nan
            cpt["absent"] += 1
        all_fp.append(fp)
    logging.info("counter: %s", cpt)
    df["fullpath"] = all_fp
    if remove_empty_lines:
        df = df.dropna()
    logging.info("%s", df)
    # write to disk
    df["fullpath"].to_csv(output, index=False, header=False)
    logging.info("output : %s", output)
    return df


def entrypoint():
    args = parseargs()
    main(
        verbose=args.verbose,
        input=args.input,
        output=args.output,
        check_existence=args.check_existence,
        remove_empty_lines=args.remove_empty_lines,
    )


if __name__ == "__main__":
    entrypoint()
