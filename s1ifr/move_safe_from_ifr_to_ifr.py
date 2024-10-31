"""
A. Grouazel
Oct 2024
script to be used with SLURM or PBS to rsync a single safe
typical use case: I want to sync lots of SAFE in scratch into a datawork directory
"""
import os
import pdb
import subprocess
import logging
import argparse
from s1ifr.explodesafename import ExplodeSAFE

def add_trailing_slash(path):
    return path if path.endswith('/') else path + '/'

def get_parent_destination_safe_path(source_safe,outputdir):
    """
    return the parent directory where to store the SAFE

    @param source_safe: str
    @param outputdir: str
    @return:  complet_dest_path str
    """
    obj = ExplodeSAFE(os.path.basename(source_safe))
    obj.get('startdate')
    parent_dest_path=  os.path.join(outputdir,obj.get('startdate').strftime('%Y'),obj.get('startdate').strftime('%j'))
    parent_dest_path = add_trailing_slash(parent_dest_path)
    logging.info('parent_dest_path : %s',parent_dest_path)
    return parent_dest_path


def sync_safe(safe_fullpath,outputdir,remove_source_file=False):
    """

    @param safe_fullpath: str
    @param outputdir: str
    @return:
        status str
    """
    logging.info('safe to sync : %s',safe_fullpath)
    if remove_source_file is True:
        rsf = "--remove-source-files"
    else:
        rsf = ""
    par_dest = get_parent_destination_safe_path(source_safe=safe_fullpath,outputdir=outputdir)
    cmd = 'rsync -avz'+rsf+' %s %s'%(safe_fullpath,par_dest)
    logging.info('command to be executed: %s',cmd)
    status = subprocess.check_call(cmd,shell=True)
    # status = -1
    logging.info('rsync status: %s',status)
    return status,cmd

def main():
    root = logging.getLogger()
    if root.handlers:
       for handler in root.handlers:
           root.removeHandler(handler)
    parser = argparse.ArgumentParser(description='safemover')
    parser.add_argument('--verbose', action='store_true', default=False)
    parser.add_argument('--input', required=True, help='SAFE path (source)')
    parser.add_argument('--outputdir', required=True, help='SAFE where to store the SAFE (destination), it should stops at the last subdir before date YYYY/JJJ/...SAFE, for instancecache/project/sarwave/data/products/tests2/slc/iw/l1b/  ')
    parser.add_argument('--removesource', required=False,
     help='True->remove SAFE from source directory [default=False]',default=False,action='store_true')
    args = parser.parse_args()
    fmt = '%(asctime)s %(levelname)s %(filename)s(%(lineno)d) %(message)s'
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format=fmt,
                            datefmt='%d/%m/%Y %H:%M:%S',force=True)
    else:
        logging.basicConfig(level=logging.INFO, format=fmt,
                            datefmt='%d/%m/%Y %H:%M:%S',force=True)
    args.input = args.input.rstrip('/') #remove trailing slash after .SAFE to be sure the rsync will also take the directory.
    if '.SAFE' not in args.input:
        raise ValueError
    sync_safe(safe_fullpath=args.input,outputdir=args.outputdir,remove_source_file=args.removesource)
    logging.info('success')

if __name__ == '__main__':
    main()
