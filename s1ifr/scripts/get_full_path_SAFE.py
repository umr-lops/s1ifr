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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="base->full")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument(
        "--input", required=True, help="input listing containing base SAFE"
    )
    parser.add_argument(
        "--archivename",
        required=False,
        choices=["scale", "datawork"],
        default="datawork",
        help="name of the archive",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="output listing containing full path SAFE",
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
    df = pd.read_csv(args.input, names=["base"])
    all_fp = []
    cpt = defaultdict(int)
    for ii in tqdm(range(len(df["base"]))):
        safe = df["base"].iloc[ii].replace(".zip", "")
        fp = get_path_from_base_safe(
            inputa=safe, archive_name=args.archivename
        )
        if fp is not None:
            pass
            cpt["ok"] += 1
        else:
            fp = np.nan
            cpt["absent"] += 1
        all_fp.append(fp)
    logging.info("counter: %s", cpt)
    df["fullpath"] = all_fp
    logging.info("%s", df)
    # write to disk
    df["fullpath"].to_csv(args.output, index=False, header=False)
    logging.info("output : %s", args.output)
