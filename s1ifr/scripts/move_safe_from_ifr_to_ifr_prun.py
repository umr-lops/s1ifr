#!/home1/datawork/agrouaze/conda_envs2/envs/py2.7_cwave/bin/python
""" """

import sys

print(sys.executable)
import getpass
import logging
import os
import subprocess


def main():
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    import argparse

    parser = argparse.ArgumentParser(description="start prun")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--outputdir", help="outputdir destination", required=True)
    parser.add_argument(
        "--listinginputsafe",
        help="listing containing paths of the safe to sync",
        required=True,
    )
    parser.add_argument(
        "--removesource",
        required=False,
        help="True->remove SAFE from source directory [default=False]",
        default=False,
        action="store_true",
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
    prunexe = "/appli/prun/bin/prun"
    lines = open(args.listinginputsafe).readlines()
    cpt = len(lines)
    logging.info("number of SAFE to be sync : %i", cpt)
    tmplisting = os.path.join(
        "/home1/scratch/",
        getpass.getuser(),
        "temporary_listing_sync_safe_sentinel1.txt",
    )
    fud = open(tmplisting, "w")
    for ll in lines:
        if args.removesource is True:
            ll2 = ll.replace("\n", "") + " " + args.outputdir + " --removesource"
        else:
            ll2 = ll.replace("\n", "") + " " + args.outputdir
        # new_lines.append(ll2)
        fud.write(ll2 + "\n")
    fud.close()
    logging.info("temporary listing update : %s", tmplisting)

    # initial listing
    # current_directory = os.getcwd()
    pbs = os.path.join(os.path.dirname(__file__), "move_safe_from_ifr_to_ifr.pbs")
    # call prun
    opts = " --split-max-jobs=50 --background -e "
    py2 = "/home1/datawork/agrouaze/conda_envs2/envs/py2.7_cwave/bin/python "
    cmd = py2 + prunexe + opts + pbs + " " + tmplisting
    logging.info("cmd to cast = %s", cmd)
    st = subprocess.check_call(cmd, shell=True)
    logging.info("status cmd = %s", st)


if __name__ == "__main__":
    main()
