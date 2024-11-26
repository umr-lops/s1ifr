"""
#clean multiple occurencies of the same SAFE file in sentinel1 data
#version of clean_sentinel1_duplicates.py that is called by the sentinel1 pieuvre (ventillation of data)
# agrouaze
# april 2014
#perm=775
@usage: 
find $PWD -maxdepth 1 -name '*SAFE' | python /home/agrouaze/git/mpc-sentinel/mpc-sentinel/mpcsentinellibs/data_collect/clean_sentinel1_duplicates_function.py
"""
import sys,os
import datetime
from lxml import etree
import fnmatch
import numpy as np
import logging
import collections
from s1ifr.quarantine_management import quarantine_ticket

def get_ending_processing_time(safe_full_path):
    pattern = '/metadataObject/metadataWrap/xmlData/{http://www.esa.int/safe/sentinel-1.0}processing'
    path_manifest = os.path.join(safe_full_path,'manifest.safe')
    tmp = datetime.datetime(2014,1,1) #dummy value
    if os.path.isfile(path_manifest) and os.path.getsize(path_manifest)>0:
        tree = etree.parse(path_manifest)
        processingdates = tree.findall('./'+pattern)
        processingdates = processingdates[0]
        tmp = processingdates.attrib['stop']
        tmp = datetime.datetime.strptime(tmp,'%Y-%m-%dT%H:%M:%S.%f')
    return tmp

def spot_dupli_core(safebasename,repdata):
    """
    :input:
        safebasename (str) S1.......SAFE
        repdata (str) archive where are store possible duplicate
    :output:
    
    :purpose:
    list duplicate and
    look at the processing date of each of them to tell which is the latest """
    
    begninig = safebasename[0:-10]
    logging.debug('begninig = %s',begninig)
    indice_latest_processing = None
    potentialoccurenceies = []
    stoptimes = None
    for root, dirnames, filenames in os.walk(repdata):
        #print filenames
        for filename in fnmatch.filter(dirnames, begninig+'*.SAFE'):
            potentialoccurenceies.append(os.path.join(root, filename))
    if potentialoccurenceies!=None and len(potentialoccurenceies)>1:
        indice_latest_processing,potentialoccurenceies,stoptimes = latest_safe_processed(potentialoccurenceies)
    return indice_latest_processing,potentialoccurenceies,stoptimes

def latest_safe_processed(duplicates_list):
    stoptimes = np.array([])
    for yy,pot in  enumerate(duplicates_list):
        logging.debug( 'duplicate %s %s',pot,yy)
        tmp = get_ending_processing_time(pot)
        stoptimes = np.append(stoptimes,tmp)
    indice_latest_processing = np.argmax(stoptimes)
    logging.debug('indice of the file with the latest processing date %s',indice_latest_processing)
    return indice_latest_processing,duplicates_list,stoptimes


def CheckDuplicate(fileTobechecked,archive='datarmor_mpc',dryrun=True):
    '''
    delete SAFE with same acquisition dates and oldest processing time
    @input: 
        fileTobechecked (str): fullpath of the .SAFE to be checked
        archive (str): mpc or datarmor_mpc
    :output:

    '''
    cpt_deleted = 0
    logging.debug('test duplication of %s',fileTobechecked)
    if '.tar' in fileTobechecked:
        fileTobechecked = fileTobechecked.strip('.tar')
    tmpbase = os.path.basename(fileTobechecked)
    repdata = os.path.dirname(fileTobechecked)
    indice_latest_processing,potentialoccurenceies,ending_processing_times = spot_dupli_core(tmpbase,repdata)
    if potentialoccurenceies is not None and len(potentialoccurenceies)>1:
        logging.debug('%s duplicates found and will be removed',len(potentialoccurenceies))
        for yy,pot in  enumerate(potentialoccurenceies):
            if yy!=indice_latest_processing:
                cpt_deleted += 1
                logging.debug('to delete %s',pot)
                if dryrun is True:
                    pass
                else:
                    quarantine_ticket(pot,archive) #added feb 2019 to delete purely the safe

                
    else:
        logging.debug('no duplicate found')
    logging.debug('end of the sentinel duplicate check')
    return cpt_deleted

def main():
    import argparse
    parser = argparse.ArgumentParser(description='clean SAFE duplicate')
    parser.add_argument('--verbose', action='store_true',default=False)
    parser.add_argument('--dryrun', action='store_true', default=False,help='[default = False], True -> data is not moved nor deleted')
    parser.add_argument('--safe',required=True,action='store',help='SAFE path to test')
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-5s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
    else:
        logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)-5s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
    cpt = collections.defaultdict(int)
    logging.info('start the check')
    # for safefull in sys.stdin:
    cpt_deleted = CheckDuplicate(fileTobechecked=args.safe,dryrun=args.dryrun)
    cpt['total_safe_analysed'] += 1
    cpt['total_safe_removed'] += cpt_deleted
    if cpt_deleted==0:
        cpt['total_acqui_already_ok'] += 1
    else:
        cpt['total_acqui_already_fixed'] += 1
    if cpt['total_safe_analysed']%100==1:
        logging.info('counter for duplicate fixing S1: %s',cpt)
    logging.info('fin script : %s',cpt)

if __name__ == '__main__':
    main()