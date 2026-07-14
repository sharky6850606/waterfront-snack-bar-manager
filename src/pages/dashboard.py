import pandas as pd
import streamlit as st

from ..calculations import operating_result
from ..config import money, now, samoa_datetime
from ..data_service import combined_financial_data, expense_breakdown
from ..ui_components import page_header, pnl_summary_card


def _total(rows, field):
    return sum(float(row.get(field) or 0) for row in rows)


def render():
    page_header("Dashboard","A clear view of sales, operating costs, payroll, and business performance in Samoa time.")
    today = now().date().isoformat()
    month = today[:7]
    datasets = combined_financial_data()
    sales, expenses, rent, payroll, audit = datasets["Sales"], datasets["Expenses"], datasets["Rent"], datasets["Payroll_Runs"], datasets["Audit_Log"]
    st.caption("Data source: legacy history plus structured application records. New application entries take precedence on matching dates; PDF links and inventory-related tabs are ignored.")
    sales_to_date = [r for r in sales if str(r["Date"]) <= today]
    expenses_to_date = [r for r in expenses if str(r["Date"]) <= today]
    rent_to_date = [r for r in rent if str(r["Payment_Date"]) <= today]
    payroll_to_date = [r for r in payroll if str(r["Pay_Date"]) <= today and r["Status"] == "Finalized"]
    all_expenses = expense_breakdown(expenses_to_date)
    all_values = [_total(sales_to_date, "Sales_Amount"), all_expenses["Operating_Total"], _total(rent_to_date, "Amount"), _total(payroll_to_date, "Gross_Total")]

    st.subheader("From Start to Today")
    all_metrics = [
        ("Total sales", all_values[0]), ("Total operating expenses", all_values[1]),
        ("Owner drawings", all_expenses["Drawings"]),
        ("Total rent", all_values[2]), ("Total gross payroll", all_values[3]),
        ("Estimated operating result", operating_result(*all_values)),
        ("Today's sales", _total([r for r in sales_to_date if r["Date"] == today], "Sales_Amount")),
    ]
    for column, (label, value) in zip(st.columns(3) * 3, all_metrics):
        column.metric(label, money(value))
    pnl_summary_card(all_values[0],all_expenses,all_values[2],all_values[3],operating_result(*all_values),money)
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
    month_metrics = [("Sales", month_values[0]), ("Operating expenses", month_values[1]), ("Owner drawings", month_expenses["Drawings"]), ("Rent", month_values[2]), ("Gross payroll", month_values[3]), ("Estimated operating result", operating_result(*month_values))]
    for column, (label, value) in zip(st.columns(3) * 2, month_metrics):
        column.metric(label, money(value))
    st.caption("Estimated operating results are internal management estimates, not audited profit. Use Refresh Data after changing a legacy worksheet to pull updates immediately.")

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
