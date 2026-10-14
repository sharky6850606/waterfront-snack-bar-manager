from decimal import Decimal
from src.calculations import estimated_cash_position,payroll_line,operating_result
def test_clarence():
 r=payroll_line(40,"7.50","0.10","0.01"); assert r["Gross_Pay"]==Decimal("300.00"); assert r["NPF_Amount"]==Decimal("30.00"); assert r["ACC_Amount"]==Decimal("3.00"); assert r["Net_Pay"]==Decimal("267.00")
def test_hayley(): assert payroll_line(40,5,.1,.01)["Net_Pay"]==Decimal("178.00")
def test_half_up(): assert payroll_line(1,"1.005",0,0)["Gross_Pay"]==Decimal("1.01")
def test_result(): assert operating_result(1000,100,200,300)==Decimal("400.00")
def test_cash_position_after_startup_and_drawings(): assert estimated_cash_position(1000,300,50,25)==Decimal("725.00")
def test_optional_overtime_and_public_holiday():
 r=payroll_line(40,"10","0.10","0.01",overtime_hours=2,public_holiday_hours=3); assert r["Normal_Pay"]==Decimal("400.00"); assert r["Overtime_Pay"]==Decimal("30.00"); assert r["Public_Holiday_Pay"]==Decimal("60.00"); assert r["Gross_Pay"]==Decimal("490.00")

