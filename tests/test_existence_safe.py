import pytest

from s1ifr.existence_safe import product_is_present_at_ifremer

test = "S1A_IW_GRDH_1SDH_20170503T103130_20170503T103158_016416_01B304_C899.SAFE"
test1 = "S1A_IW_GRDH_1SDH_20170503T103130_20170503T103158_016416_01B304_C899"
test2 = "S1B_IW_SLC__1SDV_20171103T020615_20171103T020642_008111_00E545_CAD9"
test3 = "S1B_IW_SLC__1SDV_20171103T020615_20171103T020642_008111_00E545_CAD9"
tests = [test, test1, test2, test3]


@pytest.mark.parametrize("safe_basename", tests)
def test_products_existence_usage(safe_basename):
    flag_continue, existing_storage, archive = product_is_present_at_ifremer(
        safe_basename=safe_basename
    )
    print("flag_continue", flag_continue)
    print("existing_storage", existing_storage)
    print("archive", archive)
    assert True
