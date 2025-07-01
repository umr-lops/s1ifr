"""
author: Antoine Grouazel
usage:
import get_path_from_base_SAFE
get_path_from_base_SAFE.get_path_from_base_SAFE()

"""
import sys
import os
#from explodesafename import ExplodeSAFE
from SAFEsortingfunctions import WhichArchiveDir
#from shared_information import data_dir_s1a,data_dir_s1b
def get_safe_basename_from_fullpath_measu(fullpathmeasu):
    """

    :param fullpathmeasu:
    :return:
    """
    basename_safe = os.path.basename(os.path.abspath(os.path.join(fullpathmeasu,os.path.pardir,os.path.pardir)))
    return basename_safe
    


def get_path_from_base_SAFE(inputa):
    """

    :param inputa: (str) for instance S1A_IW_OCN__2SDV_20150731T222653_20150731T222719_007061_0099AE_B180.SAFE
    :return:
        final_path (str): full path in IFREMER archive of the given Sentinel-1 SAFE
    """
    if '.SAFE' not in inputa:
        inputa += '.SAFE'
    dira = WhichArchiveDir(inputa)
    final_path = os.path.join(dira,inputa)
    return final_path

if __name__ == '__main__':
    #input is supposed to be a SAFE "S1A....SAFE"
    input_safe = sys.argv[1]
    final_path = get_path_from_base_SAFE(input_safe)
    print(final_path)
