from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
def D(value): return Decimal(str(value or 0))
def q(value): return D(value).quantize(CENT, rounding=ROUND_HALF_UP)
def payroll_line(hours, hourly_rate, npf_rate, acc_rate, overtime_hours=0, public_holiday_hours=0):
    hourly=q(hourly_rate); normal_hours=q(hours); overtime_hours=q(overtime_hours); holiday_hours=q(public_holiday_hours)
    overtime_rate=q(hourly*D("1.5")); holiday_rate=q(hourly*D("2"))
    normal_pay=q(normal_hours*hourly); overtime_pay=q(overtime_hours*overtime_rate); holiday_pay=q(holiday_hours*holiday_rate)
    gross=q(normal_pay+overtime_pay+holiday_pay); npf=q(gross*D(npf_rate)); acc=q(gross*D(acc_rate)); net=q(gross-npf-acc)
    return {"Normal_Hours":normal_hours,"Hourly_Rate":hourly,"Normal_Pay":normal_pay,"Overtime_Hours":overtime_hours,"Overtime_Rate":overtime_rate,"Overtime_Pay":overtime_pay,"Public_Holiday_Hours":holiday_hours,"Public_Holiday_Rate":holiday_rate,"Public_Holiday_Pay":holiday_pay,"Gross_Pay":gross,"NPF_Rate":D(npf_rate),"NPF_Amount":npf,"ACC_Rate":D(acc_rate),"ACC_Amount":acc,"Net_Pay":net}
def payroll_totals(lines):
    return {k:q(sum((D(x[k]) for x in lines),D(0))) for k in ("Gross_Pay","NPF_Amount","ACC_Amount","Net_Pay")}
def operating_result(sales, expenses, rent, gross_payroll): return q(D(sales)-D(expenses)-D(rent)-D(gross_payroll))
