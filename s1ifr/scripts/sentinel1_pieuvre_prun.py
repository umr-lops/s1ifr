#!/home1/datawork/agrouaze/conda_envs2/envs/py2.7_cwave/bin/python
"""
"""
import sys

print(sys.executable)
import logging
import os
import subprocess
import getpass


def main():
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    import argparse

    parser = argparse.ArgumentParser(description="start prun")
    parser.add_argument("--verbose", action="store_true", default=False)
    parser.add_argument("--archivename", choices=['scale','datawork'], default='datawork',
                        help='archive name scale or datawork [default is datawork]',required=False)
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
    username = getpass.getuser()
    ontheflymodifiedlisting = os.path.join('/home1/scratch/',username,'tmp_listing_s1_archiving_prun_script.txt')
    fid =open(ontheflymodifiedlisting,'w')
    for uu in lines:
        safeclean = uu.replace('\n','')
        uu2 = '--input-safe '+safeclean+' --archivename '+args.archivename+' \n'
        fid.write(uu2)

    fid.close()
    logging.info('temporary listing updated : %s',ontheflymodifiedlisting)
    cpt = len(lines)
    logging.info("number of SAFE to be archive : %i", cpt)

    # initial listing
    # pbs = os.path.join(os.path.dirname(__file__), "sentinel1_pieuvre.pbs") # conda env classic
    pbs = os.path.join(
        os.path.dirname(__file__), "sentinel1_pieuvre_singularity.pbs"
    )  # using a singularity image
    # call prun
    opts = " --split-max-jobs=700 --background -e "
    py2 = "/home1/datawork/agrouaze/conda_envs2/envs/py2.7_cwave/bin/python "
    cmd = py2 + prunexe + opts + pbs + " " + ontheflymodifiedlisting
    logging.info("cmd to cast = %s", cmd)
    st = subprocess.check_call(cmd, shell=True)
    logging.info("status cmd = %s", st)


if __name__ == "__main__":
    main()
