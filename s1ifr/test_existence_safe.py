"""
methods for sorting SAFE into IFREMER archive
author: Antoine Grouazel
"""
import logging
import os
import shutil
from s1ifr.SAFEsortingfunctions import WhichArchiveDir
from quarantine_management import test_quarantine_before_download
def test_existance_of_product(safe_basename,full_path_safe=None):
    """
    check that the safe downloaded do not exist in other archive dirs
    and delete the one in spool_dir if yes
    """
    flag_continue = True
    existing_storage = None
    if safe_basename[0:2]=='S1':
        possible_archives = ['mpc']
        if ".SAFE" not in safe_basename:
            safe_basename = safe_basename+'.SAFE'
    elif safe_basename[0:2]=='S3':
        possible_archives = ['s3sral']
    else:
        raise Exception('product not handle by the poulpe')
    for archive in possible_archives:
        possible_archive = WhichArchiveDir(safe_basename,archive)
        possible_storage = os.path.join(possible_archive,safe_basename)
        if os.path.exists(possible_storage)==True:
            existing_storage = possible_storage
            logging.debug('%s is already in %s archive',possible_storage,archive)
            flag_continue = False
            if full_path_safe is not None:
                remove_file_already_in_archive(full_path_safe)
            
            break
    #add a test to see if the product is black listed in quarantine
    if full_path_safe is not None:
        flag_go_download = test_quarantine_before_download(full_path_safe,archive='datarmor_mpc')
        if flag_go_download is False:
            logging.info('%s is blacklisted',full_path_safe)
            flag_continue = False
            existing_storage = 'quarantine'
            archive = 'datarmor_mpc'
    return flag_continue,existing_storage,archive

def remove_file_already_in_archive(fulle_path_tar):
    """delete SAFE.tar files from spool when already in archive"""
    if os.path.isfile(fulle_path_tar):
        os.remove(fulle_path_tar)
    else:
        shutil.rmtree(fulle_path_tar)
    logging.info('delete %s',fulle_path_tar)
    return

if __name__ == '__main__':
    test = "S1A_IW_GRDH_1SDH_20170503T103130_20170503T103158_016416_01B304_C899.SAFE"
    test1 = "S1A_IW_GRDH_1SDH_20170503T103130_20170503T103158_016416_01B304_C899"
    test2 = "S1B_IW_SLC__1SDV_20171103T020615_20171103T020642_008111_00E545_CAD9"
    test3 = "S1B_IW_SLC__1SDV_20171103T020615_20171103T020642_008111_00E545_CAD9"
    flag_continue,existing_storage,archive = test_existance_of_product(test1)
    print("flag_continue",flag_continue)
    print("existing_storage",existing_storage)
    print("archive",archive)