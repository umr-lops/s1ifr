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

def entrypoint():
    """

    Command line interface to convert base SAFE names to full path SAFE names
    in Ifremer archive structure.
    Usage example:
        python get_full_path_SAFE.py --input base_safe_list.txt --output full_path_safe_list.txt --archivename datawork --check_existence
    """
    parser = argparse.ArgumentParser(description="base->full")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument(
        "--input",
        required=True,
        help="input listing (.txt or .lst or .csv) containing base SAFE or directly a single base SAFE",
    )
    parser.add_argument(
        "--archivename",
        required=False,
        choices=["scale", "datawork"],
        default=["scale", "datawork"],
        type=list,
        help="name of the archive [optional, default is all archives available]",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="output listing containing full path SAFE",
    )
    parser.add_argument(
        "--check_existence",
        action="store_true",
        default=False,
        help="check if the SAFE file exists, if not return None",
    )
    parser.add_argument('--remove_empty_lines', action='store_true', default=False,
                        help='remove empty lines in the output listing (can occure when check_existence is True and SAFE absent)')
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
    if args.input.endswith((".csv", ".txt", ".lst")):
        df = pd.read_csv(args.input, names=["base"])
    else:
        assert ".SAFE" in args.input
        logging.info("test a single SAFE")
        df = pd.DataFrame({"base": [args.input]})
    all_fp = []
    cpt = defaultdict(int)
    for ii in tqdm(range(len(df["base"]))):
        safe = df["base"].iloc[ii].replace(".zip", "")
        flag_safe_found = False
        for archive_name in args.archivename:
            fp = get_path_from_base_safe(
                safe_basename=safe, archive_name=archive_name, check_existence=args.check_existence
            )
            if fp is not None:
                # pass
                # cpt["ok"] += 1
                flag_safe_found = True
                break
        if not flag_safe_found:
            fp = np.nan
            cpt["absent"] += 1
        else:
            cpt["found"] += 1
        all_fp.append(fp)
    logging.info("counter: %s", cpt)
    df["fullpath"] = all_fp
    logging.info("%s", df)
    if args.remove_empty_lines:
        logging.info("removing empty lines in the output listing")
        df = df.dropna(subset=['fullpath'])
    # write to disk
    df["fullpath"].to_csv(args.output, index=False, header=False)
    logging.info("output : %s", args.output)

    

if __name__ == "__main__":
    entrypoint()