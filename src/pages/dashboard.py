import pandas as pd
import streamlit as st
from datetime import date

from ..calculations import estimated_cash_position, operating_result
from ..config import money, now, samoa_datetime
from ..data_service import combined_financial_data, expense_breakdown
from ..ui_components import page_header, pnl_summary_card


def _total(rows, field):
    return sum(float(row.get(field) or 0) for row in rows)

def _month_range(start, end):
    current=date.fromisoformat(start+"-01"); finish=date.fromisoformat(end+"-01"); months=[]
    while current<=finish:
        months.append(current.strftime("%Y-%m"))
        current=date(current.year+(current.month==12),1 if current.month==12 else current.month+1,1)
    return months


def render():
    page_header("Dashboard","A clear view of sales, operating costs, payroll, and business performance in Samoa time.")
    today = now().date().isoformat()
    month = today[:7]
    datasets = combined_financial_data()
    sales, expenses, rent, payroll, audit = datasets["Sales"], datasets["Expenses"], datasets["Rent"], datasets["Payroll_Runs"], datasets["Audit_Log"]
    startup=datasets["Startup"]
    st.caption("Data source: legacy history plus structured application records. Startup costs and income are included in cash position; capital purchases remain separate from operating expenses.")
    sales_to_date = [r for r in sales if str(r["Date"]) <= today]
    expenses_to_date = [r for r in expenses if str(r["Date"]) <= today]
    rent_to_date = [r for r in rent if str(r["Payment_Date"]) <= today]
    payroll_to_date = [r for r in payroll if str(r["Pay_Date"]) <= today and r["Status"] == "Finalized"]
    all_expenses = expense_breakdown(expenses_to_date)
    all_values = [_total(sales_to_date, "Sales_Amount"), all_expenses["Operating_Total"], _total(rent_to_date, "Amount"), _total(payroll_to_date, "Gross_Total")]
    all_operating=operating_result(*all_values)
    cash_position=estimated_cash_position(all_operating,startup["Costs"],startup["Income"],all_expenses["Drawings"])
    total_rent_paid=all_values[2]+float(startup.get("Rent") or 0)

    st.subheader("From Start to Today")
    all_metrics = [
        ("Total sales", all_values[0]), ("Total operating expenses", all_values[1]),
        ("Owner drawings", all_expenses["Drawings"]),
        ("Total rent paid", total_rent_paid), ("Total gross payroll", all_values[3]),
        ("Estimated P&L", all_operating),
        ("Other startup costs", startup.get("Non_Rent_Costs",startup["Costs"]-startup.get("Rent",0))),
        ("Startup rent (Dec & Jan)", startup.get("Rent",0)), ("Startup income", startup["Income"]),
        ("Estimated cash position", cash_position),
        ("Today's sales", _total([r for r in sales_to_date if r["Date"] == today], "Sales_Amount")),
    ]
    for column, (label, value) in zip(st.columns(3) * ((len(all_metrics)+2)//3), all_metrics):
        column.metric(label, money(value))
    startup_months=", ".join(startup.get("Rent_Coverage") or [])
    recorded_rent_months=set(startup.get("Rent_Coverage") or [])|{str(row.get("Rent_For_Month")) for row in rent_to_date if float(row.get("Amount") or 0)>0}
    previous_month=(date.fromisoformat(today).replace(day=1)-pd.Timedelta(days=1)).strftime("%Y-%m")
    expected_rent_months=set(_month_range(min(recorded_rent_months),previous_month)) if recorded_rent_months else set()
    missing_rent_months=sorted(expected_rent_months-recorded_rent_months)
    st.caption(f'Startup rent {money(startup.get("Rent",0))} covers {startup_months}; it is included in total rent paid and deducted exactly once from estimated cash position.')
    if missing_rent_months: st.warning(f'Rent has no recorded payment for: {", ".join(missing_rent_months)}. Estimated cash position does not deduct unrecorded rent.')
    payroll_marked=sum(float(row.get("Total_Shopping") or 0) for row in expenses_to_date if "payroll" in str(row.get("Notes","")).lower())
    if payroll_marked: st.info(f'Expense rows marked Payroll total {money(payroll_marked)}. They remain included as recorded purchases; confirm separately if any duplicate finalized payroll.')
    pnl_summary_card(all_values[0],all_expenses,all_values[2],all_values[3],all_operating,money,startup=startup,cash_position=cash_position)
    open_days = sum(r["Status"] == "Open" for r in sales_to_date)
    closed_days = sum(r["Status"] == "Closed" for r in sales_to_date)
    a, b, c = st.columns(3)
    a.metric("Total days open", open_days)
    b.metric("Total days closed", closed_days)
    c.metric("Average sales / open day", money(all_values[0] / open_days if open_days else 0))

    monthly = [
        [r for r in sales_to_date if str(r["Date"]).startswith(month)],
        [r for r in expenses_to_date if str(r["Date"]).startswith(month)],
        [r for r in rent_to_date if str(r["Rent_For_Month"]) == month],
        [r for r in payroll_to_date if str(r["Pay_Date"]).startswith(month)],
    ]
    month_expenses = expense_breakdown(monthly[1])
    month_values = [_total(monthly[0], "Sales_Amount"), month_expenses["Operating_Total"], _total(monthly[2], "Amount"), _total(monthly[3], "Gross_Total")]
    st.subheader("Current Month")
    month_metrics = [("Sales", month_values[0]), ("Operating expenses", month_values[1]), ("Owner drawings", month_expenses["Drawings"]), ("Rent", month_values[2]), ("Gross payroll", month_values[3]), ("Estimated P&L", operating_result(*month_values))]
    for column, (label, value) in zip(st.columns(3) * 2, month_metrics):
        column.metric(label, money(value))
    st.caption("Estimated P&L is an internal management estimate, not audited profit. Use Refresh Data after changing a legacy worksheet to pull updates immediately.")

    latest_rent = max(rent_to_date, key=lambda r: str(r["Payment_Date"]), default=None)
    latest_payroll = max(payroll_to_date, key=lambda r: str(r["Pay_Date"]), default=None)
    x, y = st.columns(2)
    x.markdown("#### Latest rent payment")
    if latest_rent:
        x.metric(str(latest_rent["Rent_For_Month"]), money(latest_rent["Amount"]))
        x.caption(f'Paid {latest_rent["Payment_Date"]} · {latest_rent.get("Payment_Method") or "Method unknown"}')
    else: x.info("No rent payments yet.")
    y.markdown("#### Latest payroll")
    if latest_payroll:
        y.metric(f'Pay date {latest_payroll["Pay_Date"]}', money(latest_payroll["Gross_Total"]))
        y.caption(f'{latest_payroll["Period_Start"]} to {latest_payroll["Period_End"]} · {latest_payroll["Status"]}')
    else: y.info("No payroll runs yet.")
    st.subheader("Recent activity")
    if audit:
        recent=[{**row,"Timestamp":samoa_datetime(row.get("Timestamp"))} for row in audit[-10:]]
        st.dataframe(pd.DataFrame(recent), width="stretch", hide_index=True)
    else:
        st.info("No activity yet.")

