# Parser tests - ONLY the explicitly documented formats pass.
from ._mini import raises
from ..calendar import EthiopianDateError
from ..utils.parser import parse_ethiopian_date


def test_numeric_day_first():
    assert parse_ethiopian_date("23/01/2019") == (2019, 1, 23)
    assert parse_ethiopian_date("23-01-2019") == (2019, 1, 23)
    assert parse_ethiopian_date("23.01.2019") == (2019, 1, 23)


def test_numeric_year_first():
    assert parse_ethiopian_date("2019-01-23") == (2019, 1, 23)
    assert parse_ethiopian_date("2019/01/23") == (2019, 1, 23)


def test_ec_suffix():
    assert parse_ethiopian_date("23/01/2019 EC") == (2019, 1, 23)
    assert parse_ethiopian_date("23/01/2019 ዓ.ም") == (2019, 1, 23)


def test_named_month():
    assert parse_ethiopian_date("23 Meskerem 2019") == (2019, 1, 23)
    assert parse_ethiopian_date("1 Pagumen 2023") == (2023, 13, 1)
    assert parse_ethiopian_date("30 Nehase 2019") == (2019, 12, 30)


def test_tuple_passthrough():
    assert parse_ethiopian_date((2019, 1, 23)) == (2019, 1, 23)


def test_rejections():
    for bad in ["", None, "hello", "32/01/2019", "31/01/2019",
                "6/13/2018",  # 6 Pagumen in a common year
                "23/13/2019x", "13/13/2019",
                "2019-01", "2019/1/2/3", "23 Meskerem", "Meskerem 2019"]:
        with raises(EthiopianDateError):
            parse_ethiopian_date(bad)


def test_all_months_have_30_days():
    # NOT a rejection: every Ethiopian month has 30 days, so "29/02/2019"
    # is Tikimt 29 - valid Ethiopian, even though it looks Gregorian-odd.
    assert parse_ethiopian_date("29/02/2019") == (2019, 2, 29)


def test_named_rejects_bad_month():
    with raises(EthiopianDateError):
        parse_ethiopian_date("23 FooMonth 2019")
