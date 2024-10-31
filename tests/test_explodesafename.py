import pytest
import datetime
from s1ifr.explodesafename import ExplodeSAFE

references = {
    "S1A_WV_OCN__2SSV_20150912T225903_20150912T231133_007688_00AAC9_9ADF.SAFE": {
        "startdate": datetime.datetime(2015, 9, 12, 22, 59, 3)
    },
}


@pytest.mark.parametrize(
    (
        "safe",
        "startdate",
    ),
    [(case, references[case]["startdate"]) for case in references],
)
def test_azimuth_angles(safe, startdate):
    inst = ExplodeSAFE(safe)
    actual_startdate = inst.get("startdate")
    assert startdate == actual_startdate
