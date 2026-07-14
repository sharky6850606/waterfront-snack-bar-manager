from src.repositories import SheetRepository
from decimal import Decimal
def test_decimal_cell(): assert SheetRepository._cell(Decimal("1.25"))==1.25
