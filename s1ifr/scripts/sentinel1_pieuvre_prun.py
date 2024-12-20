#!/home1/datawork/agrouaze/conda_envs2/envs/py2.7_cwave/bin/python
"""
"""
import sys

print(sys.executable)
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
    parser.add_argument(
        "--listinginputsafe",
        help="listing containing paths of the safe to sync",
        required=True,
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
    logging.info("number of SAFE to be archive : %i", cpt)

    # initial listing
    pbs = os.path.join(os.path.dirname(__file__), "sentinel1_pieuvre.pbs")
    # call prun
    opts = " --split-max-jobs=700 --background -e "
    py2 = "/home1/datawork/agrouaze/conda_envs2/envs/py2.7_cwave/bin/python "
    cmd = py2 + prunexe + opts + pbs + " " + args.listinginputsafe
    logging.info("cmd to cast = %s", cmd)
    st = subprocess.check_call(cmd, shell=True)
    logging.info("status cmd = %s", st)


if __name__ == "__main__":
    main()
