"""
author: Antoine Grouazel
date: 6/04/2016
:usage:
 python get_full_path_from_measurement.py date --date 20190501t003325 --sat S1A

 import get_full_path_from_measurement
 get_full_path_from_measurement.get_full_path_from_measu(measu)
"""
import os
import datetime
import glob
import logging
from s1ifr.utils import load_config

conf = load_config()
sats_acro = conf["satellites"]["longnames"]

DATE_FORMAT_MEASU = '%Y%m%dt%H%M%S'

def get_full_path_from_measu(measurement, storage='datawork')->str:
    """
    to get the full path in ifremer archive of given measurement
    :args:
        measurement (str):
        storage (str): 'scale' or 'datawork'
    """
    reso = None
    sat = measurement[0:3]
    mode = measurement.split('-')[1][0:2]
    if mode[0] == 's':
        mode = 'SM'
    else:
        mode = mode.upper()
    processing = measurement.split('-')[2].upper()
    if processing in ['OCN']:
        level = 'L2'
    else:
        level = 'L1'
    if processing in ['OCN']:
        processing = sat.upper() + '_' + mode + '_' + processing.upper() + '__2S'
    elif processing in ['SLC']:
        processing = sat.upper() + '_' + mode + '_' + processing.upper() + '__1S'
    else:
        processing = sat.upper() + '_' + mode + '_' + processing.upper() + '*_1S'
    fullsat = sats_acro[sat.upper()]
    root = os.path.join(conf['paths'][storage]['archive_esa'], fullsat)
    datestart = datetime.datetime.strptime(measurement.split('-')[5], DATE_FORMAT_MEASU)
    date_before = datestart - datetime.timedelta(days=1)
    year = datestart.strftime('%Y')
    doy = datestart.strftime('%j')
    cycle = measurement.split('-')[6].upper()
    aquicistion_id = measurement.split('-')[7].upper()
    #     product_uniq = measurement.split('-')[8].replace('.tiff','').replace('.nc','').upper()
    # S1A_WV_OCN__2SSV_20150911T122006_20150911T124054_007667_00AA41_E869.SAFE
    safe = sat.upper() + '_' + mode + '_' + processing[7:] + '*_' + cycle.upper() + '_' + aquicistion_id + '_*.SAFE'
    final = os.path.join(root, level, mode, processing, year, doy, safe, 'measurement', measurement)
    logging.debug('first pattern : %s', final)
    res = glob.glob(final)
    logging.debug('Nber of res : %s', len(res))
    if not res :
        logging.debug(
            'test the day before because some measurent can have a starting date within a safe that starts the day before')
        year = date_before.strftime('%Y')
        doy = date_before.strftime('%j')
        final = os.path.join(root, level, mode, processing, year, doy, safe, 'measurement', measurement)
        logging.debug('2nd pattern: %s', final)
        res = glob.glob(final)
        if res == []:
            logging.debug('cannot find the fullpath of %s measurement, very strange....', final)
        else:
            reso = res[0]
    else:
        reso = res[0]
    return reso


def get_full_path_from_beg_measu(piece_base_measu, return_pattern_when_no_match=False,storage='datawork'):
    """
    context: to be used to get the fullpath from the 32 char given in output of WW3
    ex: s1a-wv2-slc-vv-20160501t011151-2 (need at least the basename from 's1' up to startdate )
    """
    reso = None
    sat = piece_base_measu[0:3]

    fullsat = sats_acro[sat.upper()]
    root = os.path.join(conf['paths'][storage]['archive_esa'], fullsat)
    mode = piece_base_measu.split('-')[1][0:2]
    if mode[0] == 's':
        mode = 'SM'
    else:
        mode = mode.upper()
    processing = piece_base_measu.split('-')[2].upper()
    if processing in ['OCN']:
        level = 'L2'
    else:
        level = 'L1'
    if processing in ['OCN']:
        processing = sat.upper() + '_' + mode + '_' + processing.upper() + '__2S'
    elif processing in ['SLC']:
        processing = sat.upper() + '_' + mode + '_' + processing.upper() + '__1S'
    else:
        processing = sat.upper() + '_' + mode + '_' + processing.upper() + '*_1S'
    datestart = datetime.datetime.strptime(piece_base_measu.split('-')[4], DATE_FORMAT_MEASU)
    year = datestart.strftime('%Y')
    doy = datestart.strftime('%j')
    #     cycle = piece_base_measu.split('-')[6].upper()
    #     aquicistion_id = piece_base_measu.split('-')[7].upper()
    #     product_uniq = piece_base_measu.split('-')[8].replace('.tiff','').replace('.nc','').upper()
    # S1A_WV_OCN__2SSV_20150911T122006_20150911T124054_007667_00AA41_E869.SAFE
    safe = sat.upper() + '_' + mode + '_' + processing[7:] + '*.SAFE'
    final = os.path.join(root, level, mode, processing, year, doy, safe, 'measurement', piece_base_measu + '*')
    logging.debug('proposition full path : %s', final)
    res = glob.glob(final)
    if res == []:
        logging.info('cannot find the fullpath of this measurement, very strange....')
        if return_pattern_when_no_match:
            reso = final
    else:
        reso = res[0]
    return reso


def get_full_path_ocn_wv_from_approximate_date(datedt, sat, level='L2',storage='datawork',nb_seconds_delta=3):
    """

    method to find a WV path from a date and a SAR unit
    ok for OCN and SLC WV only

    Args:
        datedt (datetime.datetime): the date for which a WV acquisition is suspected to exist
        sat (str): SAR Sentinel-1 unit such as S1A S1B ...
        level (str): Level of processing of the WV product sought, L2 or L1 [default=L2]
        storage (str): file system where the product is suposed to be stored 'datawork' or 'scale' [optional]
        nb_seconds_delta (int): positive maximum range of search for the number of seconds of shift with respect to datedt

    Returns

        reso (str): full path of the WV measurement.
    """
    reso = None
    root = os.path.join(conf['paths'][storage]['archive_esa'], sats_acro[sat.upper()])
    mode = 'WV'

    if level == 'L2':
        processing = sat.upper() + '_' + mode + '_OCN__2S'
        prodtype = 'ocn'
        ext = '.nc'
    else:
        processing = sat.upper() + '_' + mode + '_SLC__1S'
        prodtype = 'slc'
        ext = '.tiff'

    # for ssec in range(-2,2):
    ssec = -nb_seconds_delta
    while ssec <= nb_seconds_delta and reso is None:
        curdt = datedt + datetime.timedelta(seconds=ssec)
        year = curdt.strftime('%Y')
        doy = curdt.strftime('%j')
        final = os.path.join(root, level, mode, processing, year, doy,
                             processing + '*' + curdt.strftime('%Y%m%dT') + '*SAFE', 'measurement',
                             sat.lower() + '-wv*-' + prodtype + '-*-' + curdt.strftime(DATE_FORMAT_MEASU) + '*t*' + ext)
        # logging.debug('test %s',final)
        potential = glob.glob(final)
        # logging.debug('potential nb = %s',len(potential))
        if potential == []:
            pass
            # logging.debug('cannot find the fullpath of this measurement, very strange....')
        else:
            reso = potential[0]
        ssec += 1
    return reso


def get_full_path_with_safe_and_measu(safebase, measu_base,storage='datawork'):
    """
    used when inputs are coming from the json of datavore xwave quicklook request
    :param safebase:
    :param measu_base:
    :return:
    """
    sat = measu_base[0:3].upper()
    prodtype = measu_base.split('-')[2]
    datedt = datetime.datetime.strptime(measu_base.split('-')[4], DATE_FORMAT_MEASU)
    # root = os.path.join(datarmor_archive_esa_ifremer, sats_acro[sat.upper()])
    root = os.path.join(conf['paths'][storage]['archive_esa'], sats_acro[sat.upper()])
    mode = 'WV'
    year = datedt.strftime('%Y')
    doy = datedt.strftime('%j')
    if prodtype == 'ocn':
        level = 'L2'
        processing = sat.upper() + '_' + mode + '_OCN__2S'
    else:
        level = 'L1'
        processing = sat.upper() + '_' + mode + '_SLC__1S'
    finalpath = os.path.join(root, level, mode, processing, year, doy, safebase, 'measurement', measu_base)
    return finalpath


if __name__ == '__main__':
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    import argparse

    parser = argparse.ArgumentParser(description='test get_full_path...')
    parser.add_argument('--verbose', action='store_true', default=False)
    subparsers = parser.add_subparsers()
    dico_subparsers = {}
    chco = {"base": 'search from basename',
            "date": "search from date",
            }
    for subcmd in chco:
        dico_subparsers[subcmd] = subparsers.add_parser(subcmd, help='%s' % chco[subcmd])
        dico_subparsers[subcmd].set_defaults(which=subcmd)
    #     dico_subparsers['GEN'] = subparsers.add_parser('GEN', help='generate the netcdf from trackfile (old procedure) ')
    dico_subparsers['date'].add_argument('--date', type=str, help='YYYYmmddtHHMMSS')
    dico_subparsers['date'].add_argument('--sat', type=str, help='S1A or S1X...')
    dico_subparsers['date'].add_argument('--level', type=str, help='L1 or L2...')
    dico_subparsers['base'].add_argument('--input', type=str, help='s1a-wv1-... L1 or L2',
                                         required=False,default=None)
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-5s %(message)s',
                            datefmt='%d/%m/%Y %H:%M:%S')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-5s %(message)s',
                            datefmt='%d/%m/%Y %H:%M:%S')
    logging.debug('start the test')
    if args.which == 'base':
        if args.input is None:
            lst = ['s1a-wv1-ocn-vv-20150911t123908-20150911t123911-007667-00aa41-079.nc',
                       's1b-ew-grd-vv-20151216t105548-20151216t105648-009066-00003f-001.tiff',
                       's1a-wv2-ocn-vv-20160101t041326-20160101t041328-009295-00d6cb-028.nc',
                       's1b-wv1-ocn-vv-20160901t003557-20160901t003600-001868-002e16-005.nc' ]
            expected_res = ['/home/datawork-cersat-public/project/mpc-sentinel1/data/esa/sentinel-1a/L2/WV/S1A_WV_OCN__2S/2015/254/S1A_WV_OCN__2SSV_20150911T122006_20150911T124054_007667_00AA41_E869.SAFE/measurement/s1a-wv1-ocn-vv-20150911t123908-20150911t123911-007667-00aa41-079.nc',
                            '/home/datawork-cersat-public/project/mpc-sentinel1/data/esa/sentinel-1b/L1/EW/S1B_EW_GRDM_1S/2015/350/S1B_EW_GRDM_1SDV_20151216T105548_20151216T105648_009066_00003F_FC8D.SAFE/measurement/s1b-ew-grd-vv-20151216t105548-20151216t105648-009066-00003f-001.tiff',
                            '/home/datawork-cersat-public/project/mpc-sentinel1/data/esa/sentinel-1a/L2/WV/S1A_WV_OCN__2S/2016/001/S1A_WV_OCN__2SSV_20160101T040650_20160101T042906_009295_00D6CB_B024.SAFE/measurement/s1a-wv2-ocn-vv-20160101t041326-20160101t041328-009295-00d6cb-028.nc',None]
            for measurement in lst:
                get_full_path_from_measu(measurement)
                logging.debug(' %s -> %s', measurement, get_full_path_from_measu(measurement))
                assert get_full_path_from_measu(measurement) == expected_res[lst.index(measurement)]
                logging.info('test #%i : OK'%lst.index(measurement))
        else:
            measurement = args.input
            print('input', measurement)

            print('res,', get_full_path_from_measu(measurement))

    elif args.which == 'date':
        res = get_full_path_ocn_wv_from_approximate_date(datetime.datetime.strptime(args.date, DATE_FORMAT_MEASU),
                                                         args.sat, level=args.level)
        print(res)
    else:
        print('are you sure??')