"""
Author:  Antoine.Grouazel@ifremer.fr
Purpose:separate information in SAFE name sentinel1
Creation:  2014-11-28
Arguments: basename SAFE directory
note: valid also for Sentinel3 SRAL data
"""

import datetime
import logging
import re
import sys

fields = [
    "satellite",
    "mode",
    "product",
    "level",
    "polarisation",
    "startdate",
    "enddate",
    "absolute_orbit_number",
    "mission_data_take",
    "product_id",
    "kind",
]
DEFAULT_DATE_FORMAT = "%Y%m%dT%H%M%S"
SAFE_PATTERN = (
    r"^(?P<mission_id>S1[A-Z])_"
    r"(?P<mode>(?:IW|EW|WV|S[1-6]))_"
    r"(?P<type>(?:GRDH|GRDF|GRDM|SLC_|RAW_|OCN_))_"
    r"(?P<level>[0-9])(?P<class>[A-Z])(?P<pol>[A-Z]{2})_"
    r"(?P<starttime>\d{8}T\d{6})_"
    r"(?P<endtime>\d{8}T\d{6})_"
    r"(?P<orbit_no>\d{6})_"
    r"(?P<datatake_id>[A-Z0-9]{6})"
    r"(?:_(?P<id>[A-Z0-9]{4})(?:_(?P<suffix>[A-Z0-9]{3}))?)?"
    r"(?:\.SAFE)?$"
)


def check_safe_name_match_expected_s1_pattern(safename: str) -> bool:
    """Check if the given SAFE name matches the expected Sentinel-1 pattern.

    Args:
        safename: The SAFE product name to check.
    """
    match = re.match(SAFE_PATTERN, safename)
    return match, match is not None


class ExplodeSAFE:
    """input basename_safe (str) SAFE name
    only (no parent directories before neitheir children files)"""

    def __init__(self, basename_safe):
        if "/" in basename_safe:
            raise ValueError("need basename not full path")
        if basename_safe[0:2] == "S1":
            self.safename = basename_safe
            # Use SAFE regex for robust extraction of named groups

            # m = re.match(SAFE_PATTERN, self.safename)
            m, flag_is_safe = check_safe_name_match_expected_s1_pattern(
                self.safename
            )
            if flag_is_safe is False or m is None:
                raise ValueError(
                    f"S1 SAFE name does not match expected pattern: '{self.safename}'"
                )
            g = m.groupdict()

            self.satellite = g.get("mission_id")
            self.mode = g.get("mode")
            self.product = g.get("type")
            self.level = g.get("level")
            # 'kind' previously was a single char at pos 13; use 'class' if available
            self.kind = g.get("class")
            self.polarisation = g.get("pol")
            try:
                self.startdate = datetime.datetime.strptime(
                    g.get("starttime"), DEFAULT_DATE_FORMAT
                )
                self.enddate = datetime.datetime.strptime(
                    g.get("endtime"), DEFAULT_DATE_FORMAT
                )
            except Exception as e:
                raise ValueError(
                    f"Failed to parse start/end dates from SAFE name '{self.safename}': {e}"
                )

            self.absolute_orbit_number = g.get("orbit_no")
            self.duration = (self.enddate - self.startdate).total_seconds()
            self.sensor = "CbandRadar"
            self.mission_data_take = g.get("datatake_id")  # datatake id
            self.product_id = g.get("id")  # unique id (processing ID)
            self.production_status = "operational"
            self.cycle_number = None
            self.relative_orbit_number = None

        elif basename_safe[0:2] == "S3":
            self.safename = basename_safe
            splitos = self.safename.split("_")
            self.satellite = splitos[0]
            self.mode = None
            self.sensor = splitos[1]
            self.product = splitos[3]
            self.duration = splitos[10]
            self.level = splitos[2]
            self.kind = None
            self.polarisation = None
            self.startdate = datetime.datetime.strptime(
                splitos[7], DEFAULT_DATE_FORMAT
            )
            self.enddate = datetime.datetime.strptime(
                splitos[9], DEFAULT_DATE_FORMAT
            )
            self.absolute_orbit_number = None
            self.cycle_number = splitos[11]
            self.relative_orbit_number = splitos[12]
            self.mission_data_take = splitos[9]  # product id
            self.product_generating_center = splitos[18]
            self.product_id = splitos[
                10
            ]  # unique id for a given product id( you can have the same for different product_id)
            productions_status_code = {
                "O": "operational",
                "F": "reference",
                "D": "development",
                "R": "reprocessing",
            }
            self.production_status = productions_status_code[splitos[19]]

    def props(self):
        return [i for i in self.__dict__.keys() if not i.startswith("_", 0, 1)]

    def get(self, info):
        #         if info in fields:
        res = getattr(self, info)
        #         else:
        #             logging.error('no field %s in safe name',info)
        #             res = None
        return res


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) > 1:
        safe = sys.argv[1]
    else:
        safe = None

    if safe is None:
        for safe in [
            "S1A_IW_SLC__1SDV_20141128T231212_20141128T231239_004275_005C3C_7F6C.SAFE",
            "S1B_EW_GRDM_1SDH_20210615T120001_20210615T120121_000000_000000_0000.SAFE",
            "S1D_EW_RAW__0SDH_20220301T150000_20220301T150120_000000_000000_0000.SAFE",
            "S1E_S1_OCN__2SDH_20220301T150000_20220301T150120_000000_000000_0000.SAFE",
            "S1A_WV_SLC__1SDV_20170615T120001_20170615T120021_014275_017C3C_7F6C.SAFE",
            "S1B_WV_OCN__2SDH_20210615T120001_20210615T120121_000000_000000_0000.SAFE",
            "S1B_WV_OCN__2SDH_20210615T120001_20210615T120121_000000_000000",
            "S1A_IW_GRDH__1SDV_20200101T061511_20200101T061538_030603_038187",
        ]:
            obj = ExplodeSAFE(safe)
            print("OK for safe=", safe, obj.startdate, obj.product_id)
    else:
        if "S3" == safe:
            # attention fichiers coupe en demi orbit mais une seul numero de cycle
            safe = "S3A_SR_2_WAT____20170124T120058_20170124T121058_20170124T140548_0599_013_294______MAR_O_NR_002.SEN3"
        else:
            logging.info("%s", safe)
            obj = ExplodeSAFE(safe)
            print(obj.get("startdate"))
            #     for ff in fields:
            for ff in obj.props():
                val = obj.get(ff)
                logging.debug("info %s => %s", ff, val)
            print("start date=", obj.startdate)
