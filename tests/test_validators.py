import pytest
from src.validators import parse_date,validate_sales,validate_period,ValidationError
from src.config import samoa_datetime
def test_dates(): assert parse_date("31/03/26")=="2026-03-31"
def test_closed_zero(): assert validate_sales("Closed",99)==0
def test_bad_period():
 with pytest.raises(ValidationError): validate_period("2026-02-02","2026-01-01")
def test_utc_timestamp_displays_in_samoa(): assert samoa_datetime("2026-07-13T00:00:00+00:00")=="13/07/2026 01:00:00 PM Samoa"
