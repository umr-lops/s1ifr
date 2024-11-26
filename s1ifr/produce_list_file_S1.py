"""
author: Antoine Grouazel
purpose: optimized tool to produce different kind of Sentinel-1 files list (measurement,SAFE)
 depending on various query arguments (mode,polarisation,level,archive,...) 
creation: 2014
"""
import os
import sys
import logging
import fnmatch
import datetime
import glob
from dateutil import rrule
from s1ifr.shared_information import sats_acro
# import pdb
from s1ifr.SAFEsortingfunctions import ADDITIONAL_ARCHIVES
sat = {"S1A":"sentinel-1a","S1B":'sentinel-1b'}

def writeTheFileList(type,format,repdata,startdate,enddate,satellite,level,onlyonsea=True,write_to_file=True):
    '''
    create a list of measurement file from mpc ifremer sentinel1 archive
    type (str) aquisirion mode ex : WV
    format (str) ex:slc or grdh or grdm or ocn_
    repdata (str): path up to level directory (included)
    startdate endate (str): YYYYMMDD
    extension (str) ex: tiff
    satellite (str): S1A or S1B
    level (str) L1 or L2
    onlyonsea (bool) use landmask to keep only acquisition with a least one point on the sea
    write_to_file (bool):
    '''
#     from ceraux.landmask import Landmask
#     from ceraux.landmask_resources import LAND_MASK_PATH
#     from cerbere.datamodel.grid import Grid
#     from cerbere.datamodel.image import Image
#     from sarimage import SARImage
#     from cerbere.mapper.safegeotifffile import SAFEGeoTiffFile
    if len(format)==3:
        format_safe = format+'_'
    else:
        format_safe = format
    format_file = format
    subtype = satellite+'_'+type+'_'+format_safe.upper()+'_'+level[1]+'S'
    repdatatype = os.path.join(repdata , type ,subtype)
    logging.debug('rep %s',repdatatype)
    if level == 'L1':
        extension = 'tiff'
    elif level=='L2':
        extension = 'nc'
    filout = '/tmp/'
    pattern = satellite.lower()+'*'+format_file[0:3].lower()+'*.'+extension
    #logging.debug('pattern sought %s',pattern)
    logname = satellite+'_'+type+'_'+format_safe+'_'+startdate+'_'+enddate+'_'+extension+'_onsea_'+str(onlyonsea)+'.lst'


    startdate = datetime.datetime.strptime(startdate,'%Y%m%d')
    #logging.debug('type date %s',startdate)
    enddate = datetime.datetime.strptime(enddate,'%Y%m%d')
    if startdate == enddate:
        enddate += datetime.timedelta(hours=24)
#     if onlyonsea:
#         #landmask
#     #     instanceLD = Landmask(filename=LAND_MASK_PATH+'NAVO-lsmask-world8-var.dist5.5.nc')
#         instanceLD = Landmask(filename=LAND_MASK_PATH+'mwf-ers-mask.nc')
#     
    tifflist = []
    if write_to_file:
        logpath = filout+logname
        fid = open(logpath,'w')
    else:
        logpath = None
#     classinstance = PolygonIntersection()
#     year_start = startdate.year
#     year_end = enddate.year
#     vector_year = range(year_start,year_end+1)
#     startdoy = startdate.timetuple().tm_yday
#     enddoy = enddate.timetuple().tm_yday
#     logging.debug('startdoy %s enddoy %s ',startdoy,enddoy)
#     vector_doy = range(startdoy,enddoy+1)
#     logging.debug('vector doy: %s',vector_doy)
    for dd in rrule.rrule(rrule.DAILY,dtstart=startdate,until=enddate):
        yy = str(dd.year)
        doy = str(dd.timetuple().tm_yday).zfill(3)
#     for yy in vector_year:
#         for doy in vector_doy:
        repdatatype_date = os.path.join(repdatatype,yy,doy+'/')
        #logging.debug('rep to search %s ',repdatatype_date)
        for root, dirnames, filenames in os.walk(repdatatype_date):
#                 logging.debug('filenames %s',filenames)
            for filename in fnmatch.filter(filenames,pattern):
                fullpath = os.path.join(root,filename)
                #logging.debug('path %s',fullpath)
#                 datesar = filename[15:23]
                datesar = filename.split('-')[4]
                #logging.debug('datesar : %s',datesar)
                datesar = datetime.datetime.strptime(datesar,'%Y%m%dt%H%M%S')
                #logging.debug('datesar %s',datesar)
                if datesar>= startdate and datesar <= enddate:
                    tifflist.append(fullpath)
                    if write_to_file:
                        fid.write(fullpath+'\n')
    if write_to_file:
        fid.close()
        logging.info('output %s',logpath)
    return logpath,tifflist

def _writeTheDirList_subsub(repdata,startdate,enddate,satellite,level,type,format):
    """everything is known"""
    repdatatype = os.path.join(repdata,format+'/')
    logging.info('rep %s',repdatatype)
    extension = 'SAFE'
    pattern = satellite+'*.'+extension
    logging.debug('pattern: %s',pattern)
    startdate = datetime.datetime.strptime(startdate,'%Y%m%d')
    enddate = datetime.datetime.strptime(enddate,'%Y%m%d')
    listSAFE = []
    for d in rrule.rrule(rrule.DAILY, dtstart=startdate, until=enddate):
        year_str = str(d.year)
        doy = str(d.timetuple().tm_yday).zfill(3)
        rep_dated = os.path.join(repdatatype,year_str,doy+'/')
        logging.debug('rep_dated %s',rep_dated)
        listSAFE = listSAFE+glob.glob(rep_dated+pattern)
    return listSAFE

def _writeTheDirList_sub(repdata,startdate,enddate,satellite,level,type,format=None,category=None):
    """ the type is known and the format can be not known
    Args:
        repdata (str):
        startdate 
        enddate
        satellite (str): S1A
        level (str): L0
        type (str): WV IW ...
        format (str): GRDH  ...
    """
    if category is None:
        category = ['S']
    repdatatype = os.path.join(repdata,type+'/')
    if os.path.exists(repdatatype):
        if format is None:
            list_format = os.listdir(repdatatype)
            real_standard_list = []
            for uu in list_format:
                if uu[-1] in category:
                    real_standard_list.append(uu)
            
            listSAFE = []
            for known_format in real_standard_list:
                listSAFE = listSAFE+_writeTheDirList_subsub(repdatatype,startdate,enddate,satellite,level,type,known_format)
        else:
            listSAFE = []
            for cat in category:
                known_format = satellite+'_'+type+'_'+format+'_'+level[1]+cat
                listSAFE = listSAFE+_writeTheDirList_subsub(repdatatype,startdate,enddate,satellite,level,type,known_format)
    else:
        listSAFE = []
    return listSAFE

def writeTheDirList(startdate,enddate,satellite,level,write=True,typo=None,formato=None,archive_name='datarmor_mpc',
                    category=['S'],logfile_path=None,logdir_path=None):
    '''
    create a list of SAFE directories (basename of the SAFE only)
    Args:
        satellite (str) S1A or S1B
        startdate (str) YYYYMMDD
        level (str): L1 or L2 or L0
        write (bool):
        enddate (str) YYYYMMDD
        typo (str) IW EW SM WV
        formato (str) OCN_ SLC_ RAW_
        logfile_path (str):
        logdir_path (str):
    Returns:
        list_safe (list):
        logpath (str): 
    '''
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    repdata = os.path.join(root_archive,sat[satellite],level+'/')
    logging.debug('repdata= %s',repdata)
    logging.debug('writeTheDirList | typo=%s',typo)
    if typo is None:
        list_safe = []
        for typo_known in ['IW','EW','SM','WV']:
            list_safe = list_safe+_writeTheDirList_sub(repdata,startdate,enddate,satellite,level,typo_known,formato,category=category)
    else:
        list_safe = _writeTheDirList_sub(repdata,startdate,enddate,satellite,level,typo,formato,category=category)
    list_safe.sort()
    if write:
        if logfile_path is None:
            if logdir_path is None:
                dirout = '/home1/datahome/agrouaze/PRUN_workspace/'
            else:
                dirout = logdir_path
            logname = satellite+'_'+startdate+'_'+enddate+'_dirSAFE.lst'
            logpath = os.path.join(dirout,logname)
        else:
            if logdir_path is None:
                logpath = logfile_path
            else:
                logname = satellite+'_'+startdate+'_'+enddate+'_dirSAFE.lst'
                logpath = os.path.join(logdir_path,logname)
        fid = open(logpath,'w')
        for safe in list_safe:
            fid.write(safe+'\n')
        fid.close()
        logging.info('output %s',logpath)
    else:
        logpath = None
    logging.info('%s SAFE found',len(list_safe))
    return list_safe,logpath


def FindSARNetCDFDayBefore(nbdays,satellite,archive_name='mpc'):
    '''
    browse the mpc repositories to find the netCDF data from the X past days
    Args:
        nbdays (int): number of days to take into account before the present day
        satellite (str): sentinel-1a
        archive (str): mpc or benguela or canaries or swarp
    Returns:
        netCDF_list (list):
    NOT CALLED IN MAIN BUT USED ELSEWHERE
    '''
    logging.info('coloc for a given date %s days back',nbdays)
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    rep_data = os.path.join(root_archive,satellite,'L2/')
    now = datetime.datetime.now()
    yerterday = now - datetime.timedelta(days=nbdays)
    dateyes = datetime.datetime.strftime(yerterday,'%Y%m%d')
    logging.info('find all the %s netCDF on day %s',satellite,dateyes)
    pattern_nc = rep_data+'*/*/*/*/*/measurement/*ocn-*'+dateyes+'*.nc'
    logging.debug('pattern %s',pattern_nc)
    netCDF_list = glob.glob(pattern_nc)
    logging.info('number of netCDF found %s',len(netCDF_list))
    return netCDF_list

def FindSARNetCDFBewteen2Dates(start,stop,satellite,mode='*',archive_name='datarmor_mpc'):
    """
    start,stop (datetime)
    satellite (str) sentinel-1a or 1b
    mode (str): WV IW EW SM [default all]
    archive (str): mpc or benguela or canaries or swarp
    """
    logging.debug('looking for SAR netcdf files between %s-%s dates',start,stop)
    netCDF_list = []
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    rep_data = os.path.join(root_archive,satellite,'L2/')
#     if isinstance(start,str):
#         current_date = datetime.datetime.strptime(start,'%Y%m%d')
#         last_date = datetime.datetime.strptime(stop,'%Y%m%d')
#     else:
#         current_date = start
#         last_date = stop
    start_rule = start-datetime.timedelta(days=1) #added 26 nov 2021, because some nc are in SAF that belongs to previous day
    if start>stop:
        raise Exception('start date is > stop date')
    if start == stop:
        stop = stop+datetime.timedelta(days=1)
    cpt = 0
    cpt_out_of_bounds = 0
    logging.debug('start = %s,stop = %s,stop = %s',start,stop,stop)
    for dd in rrule.rrule(rrule.DAILY, dtstart=start_rule, until=stop):
        year = str(dd.year)
        doy = str(dd.timetuple().tm_yday).zfill(3)
        dateyes = datetime.datetime.strftime(dd,'%Y%m%d')
        pattern_nc = os.path.join(rep_data,mode,'*',year,doy,'*'+dateyes+'*.SAFE','measurement','*ocn-*.nc')
        #pattern_nc = os.path.join(rep_data,mode,'*',year,doy,'*'+dateyes+'*.SAFE','measurement','*ocn-*'+dateyes+'*.nc')
        if cpt==0:
            logging.debug('first pattern tested = %s',pattern_nc)
        tmp = glob.glob(pattern_nc)
        logging.debug('pattern %s : %s',pattern_nc,len(tmp))
        #netCDF_list = netCDF_list+tmp
        for ff in tmp:
            datestartdt = datetime.datetime.strptime(os.path.basename(ff).split('-')[4],'%Y%m%dt%H%M%S')
            if datestartdt>=start and datestartdt<=stop:
                netCDF_list.append(ff)
            else:
                cpt_out_of_bounds += 1
#         current_date = current_date + datetime.timedelta(days=1)
        cpt += 1
    logging.debug('number of netCDF found %s',len(netCDF_list))
    logging.debug('cpt_out_of_bounds : %s',cpt_out_of_bounds)
    return netCDF_list

def find_s1_measurement_between_2_dates(start, stop,product_type,archive_name='datarmor_mpc'):
    """
    
    nouvelle mouture de FindSARNetCDFBewteen2Dates plus generique et plus specifique en terme de recherche
    Args:
        start,stop (datetime):
        product_type (str): ex S1A_WV_SLC__1S
    """
    netCDF_list = []
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    satellite = product_type[0:3]
    fs = sats_acro[satellite]
    logging.debug('full sat :%s',fs)
    mode = product_type.split('_')[1]
    level = 'L'+product_type[-2:-1]
    if level =='L1':
        ext = 'measurement/*.tiff'
    elif level == 'L2':
        ext = "measurement/*.nc"
    elif level =="L0":
        ext = '*.dat'
    if start==stop:
        pass
    elif start>stop:
        raise Exception('start date is > stop date')
    logging.debug('start: %s,stop: %s',start,stop)
#     if current_date == last_date:
#         last_date = current_date+datetime.timedelta(days=1)
    for dd in rrule.rrule(rrule.DAILY, dtstart=start, until=stop):
        year = str(dd.year)
        doy = str(dd.timetuple().tm_yday).zfill(3)
        patho = os.path.join(root_archive,fs,level,mode,product_type,year,doy)
        logging.debug('path constructed: %s',patho)
        if os.path.exists(patho):
            pattern = os.path.join(patho,'*.SAFE',ext)
            logging.debug('pattern: %s',pattern)
            tmp = glob.glob(pattern)
            netCDF_list = netCDF_list+tmp
    logging.debug('number of netCDF found %s',len(netCDF_list))
    return netCDF_list

def FindSARtiffBewteen2Dates(start,stop,satellite,mode,archive_name='datarmor_mpc',processing_format='*'):
    """
    start,stop (str/datetime)
    satellite (str) sentinel-1a or 1b
    mode (list) [IW,EW,...]
    processing_format (str): GRDM or SLC_ or GRDH or GRDF or *
    """
    logging.debug('looking for SAR tiff files between %s-%s dates',start,stop)
    if isinstance(mode,str):
        mode = [mode]
    tiff_list = []
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    rep_data = os.path.join(root_archive,satellite,'L1')
#     if isinstance(start,str):
#         current_date = datetime.datetime.strptime(start,'%Y%m%d')
#         last_date = datetime.datetime.strptime(stop,'%Y%m%d')
#     else:
#         current_date = start
#         last_date = stop
    if start>stop:
        raise Exception('start date is > stop date')
#     if current_date == last_date:
#         last_date = current_date+datetime.timedelta(days=1)
    for dd in rrule.rrule(rrule.DAILY, dtstart=start, until=stop):
        year = str(dd.year)
        doy = str(dd.timetuple().tm_yday).zfill(3)
        dateyes = datetime.datetime.strftime(dd,'%Y%m%d')
        for mm in mode:
            pattern = os.path.join(rep_data,mm,'*_'+processing_format+'_1S',year,doy,'*','measurement','*'+dateyes+'*.tiff')
            tmp = glob.glob(pattern)
            logging.debug('pattern %s : %s',pattern,len(tmp))
            tiff_list = tiff_list+tmp
#         current_date = current_date + datetime.timedelta(days=1)
    logging.debug('number of tiff found %s',len(tiff_list))
    return tiff_list

def FindTiffFromDayBefore(nbdays,satellite,mode=['SM','IW','EW','WV'],archive_name='datarmor_mpc'):
    """
    browse the mpc repositories to find the tiff data from last days
    mode (list) EW IW SM WV
    NOT CALLED IN MAIN BUT USED ELSEWHERE
    """
    root_archive = ADDITIONAL_ARCHIVES[archive_name]
    sat_dir = sat[satellite]
    rep_data = os.path.join(root_archive,sat_dir,'L1/')
    ext = 'tiff'
    product_type = '1S'
    file_format = 'grd'

    now = datetime.datetime.now()
    yerterday = now - datetime.timedelta(days=nbdays)
    dateyes = datetime.datetime.strftime(yerterday,'%Y%m%d')
    logging.info('find all the %s tiff on day %s',satellite,dateyes)
#     tiff_list = glob.glob(rep_data+'*/*/*/*/*/measurement/*grd-*'+dateyes+'*.tiff')
    files_SM = []
    files_IW = []
    files_EW = []
    files_WV = []
    if 'SM' in mode:
        files_SM = glob.glob(rep_data+'SM/'+satellite+'_SM_*_'+product_type+'/*/*/*/measurement/*'+file_format+'-*'+dateyes+'*.'+ext)
        logging.info('number of tiff found for SM %s',len(files_SM))
    if 'IW' in mode:
        files_IW = glob.glob(rep_data+'IW/'+satellite+'_IW_'+file_format.upper()+'_'+product_type+'/*/*/*/measurement/*'+file_format+'-*'+dateyes+'*.'+ext)
        logging.info('number of tiff found for IW %s',len(files_IW))
    if 'EW' in mode:
        files_EW = glob.glob(rep_data+'EW/'+satellite+'_EW_'+file_format.upper()+'_'+product_type+'/*/*/*/measurement/*'+file_format+'-*'+dateyes+'*.'+ext)
        logging.info('number of tiff found for EW %s',len(files_EW))
    if 'WV' in mode:
#         if level == 'L1':
        files_WV = glob.glob(rep_data+'WV/'+satellite+'_WV_SLC__'+product_type+'/*/*/*/measurement/*slc-*'+dateyes+'*.'+ext)
        logging.info('number of tiff found for WV %s',len(files_WV))
#         elif level == 'L2':
#             files_WV = glob.glob(rep_data+'WV/'+satellite+'_WV_OCN__'+product_type+'/*/*/*/measurement/*ocn-*'+dateyes+'*.'+ext)
#             logging.info('number of tiff found for WV %s',len(files_WV))
    final_list = files_SM+files_IW+files_EW+files_WV
#     logging.debug('%s',files_list)
    logging.info('number of tiff found %s',len(final_list))
    return final_list

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
#     repdata = '/home/cercache/project/mpc-sentinel1/data/esa/sentinel-1a/L1/'
    type = 'WV'
    format = 'slc'
    startdate = '20141231'
    enddate = '20160101'
    extension = 'tiff'
    satellite='S1A'
    level = 'L2'
    write = False
#     logpath = writeTheFileList(type,format,repdata,startdate,enddate,extension)
#     writeTheFileList(type,format,repdata,startdate,enddate,extension,onlyonsea=False)
#     writeTheDirList(type,format,repdata,startdate,enddate)
#     writeTheDirList(startdate,enddate,satellite,level,write=write,type='WV',format='OCN_')
    choice_usage = ['count_SAFE','count_measurement','count_measurementv2','write_measurment_list']
    level_choice = ['L1','L2']
    format_choice = ['SLC_','GRDH','GRDF','GRDM','OCN_','RAW_']
    satellite_choice = ['S1A','S1B','S1C']
    mode_choice = ['WV','EW','IW','SM']
    from optparse import OptionParser
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler) 
#     possibles_archives = ADDITIONAL_ARCHIVES.keys()
    possibles_archives = [rere for rere in ADDITIONAL_ARCHIVES]
    parser = OptionParser()
    parser.add_option("-v","--verbose",
                        action="store_true",
                        dest="verbose",default=False,
                        help="verbose mode")
    parser.add_option("-b","--begining",
                        action="store", type="string",
                        dest="startdate", metavar="string",
                        help="starting date YYYYMMDD")
    parser.add_option("-e","--enddate",
                        action="store", type="string",
                        dest="enddate", metavar="string",
                        help="stoping date YYYYMMDD")
    parser.add_option("-u","--usage",
                        action="store", type="choice",choices=choice_usage,
                        dest="usage", metavar="string",
                        help="what do you want: %s ?"%choice_usage)
    parser.add_option("-l","--level",
                        action="store", type="choice",choices=level_choice,
                        dest="level", metavar="string",
                        help="which level do you want: %s ?"%level_choice)
    parser.add_option("-f","--format",
                        action="store", type="choice",choices=format_choice,
                        dest="format", metavar="string",
                        help="which format do you want: %s ?"%format_choice)
    parser.add_option("-o","--outputlisting",
                      action="store",type="string",
                      dest="outputlisting",metavar="string",
                      help="file where to write result")
    parser.add_option("-s","--satellite",
                        action="store", type="choice",choices=satellite_choice,
                        dest="satellite", metavar="string",
                        help="which satellite do you want: %s ?"%satellite_choice)
    parser.add_option("-m","--mode",
                        action="store", type="choice",choices=mode_choice,
                        dest="mode", metavar="string",
                        help="which mode do you want: %s ?"%mode_choice)
    parser.add_option("-a","--archive",
                        action="store", type="choice",choices=possibles_archives,
                        dest="archive", metavar="string",
                        help="which archive do you want: %s ? [optional, default is datarmor_mpc ]"%ADDITIONAL_ARCHIVES.keys())
    (options, args) = parser.parse_args()
    if options.startdate is None or options.enddate is None:
        raise Exception('you have to specify -e and -s args')
    startdt = datetime.datetime.strptime(options.startdate,'%Y%m%d')
    stopdt = datetime.datetime.strptime(options.enddate,'%Y%m%d')
    if options.level is None:
        raise Exception('you have to specify --level args')
    if options.archive is None:
        archive_name = 'datarmor_mpc'
    else:
        archive_name = options.archive
    if options.verbose==True:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    if options.usage=='count_SAFE':
        writeTheDirList(options.startdate,options.enddate,options.satellite,level=options.level,typo=options.mode,
                        formato=options.format,archive_name=archive_name,logfile_path=options.outputlisting)
    elif options.usage == 'count_measurement':
        if options.level=='L1':
            tiff_list = FindSARtiffBewteen2Dates(startdt,stopdt,sat[options.satellite],[options.mode],
                                                 archive_name=archive_name,processing_format=options.format)
            logging.info('Nber of measurement: %s',len(tiff_list))
        elif options.level=='L2':
            netCDF_list = FindSARNetCDFBewteen2Dates(startdt,stopdt,sat[options.satellite],options.mode,archive_name=archive_name)
            logging.info('Nber of measurement: %s',len(netCDF_list))
    elif options.usage == 'write_measurment_list':
        sat_dir = sat[options.satellite]
        root_archive = ADDITIONAL_ARCHIVES[archive_name]
        rep_data = os.path.join(root_archive,sat_dir,options.level)
        writeTheFileList(options.mode,options.format,rep_data,options.startdate,options.enddate,options.satellite,
                         options.level,onlyonsea=False,write_to_file=True)
    elif options.usage == 'count_measurementv2':#not better simply more rafined
        product_type = options.satellite+'_'+options.mode+'_'+options.format+'_'+options.level[1]+'S'
        logging.info('product type: %s',product_type)
        listmesu = find_s1_measurement_between_2_dates(startdt, stopdt, product_type, archive_name='datarmor_mpc')
        print(len(listmesu))
    else:
        raise Exception('Bad argument usage')
    
