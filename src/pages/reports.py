import pandas as pd
import streamlit as st

from ..calculations import estimated_cash_position, operating_result
from ..config import money, now
from ..data_service import combined_financial_data, expense_breakdown, filter_financial_data
from ..exports import complete_backup, csv_bytes, excel_bytes
from ..pdf_generator import financial_report_pdf
from ..ui_components import page_header


def _total(rows, field):
    return sum(float(row.get(field) or 0) for row in rows)


def _payroll_export(runs, details):
    by_id = {str(r["Payroll_ID"]): r for r in runs}
    output = []
    for detail in details:
        run = by_id.get(str(detail["Payroll_ID"]), {})
        output.append({"Payroll_ID": detail.get("Payroll_ID"), "Period_Start": run.get("Period_Start"), "Period_End": run.get("Period_End"), "Pay_Date": run.get("Pay_Date"), **detail})
    return output


def render():
    page_header("Reports", "Select an inclusive date range and download matching legacy and application records in reliable formats.")
    date_a, date_b = st.columns(2)
    start = date_a.date_input("From", now().date().replace(day=1), key="report_from")
    end = date_b.date_input("To", now().date(), key="report_to")
    if start > end:
        st.error("The From date must not be after the To date.")
        return
    lo, hi = start.isoformat(), end.isoformat()
    datasets = combined_financial_data()
    startup = datasets["Startup"]
    selected = filter_financial_data(datasets, lo, hi)
    sales, expenses, rent = selected["Sales"], selected["Expenses"], selected["Rent"]
    runs, details = selected["Payroll_Runs"], selected["Payroll_Details"]
    expense_totals = expense_breakdown(expenses)
    values = [_total(sales, "Sales_Amount"), expense_totals["Operating_Total"], _total(rent, "Amount"), _total(runs, "Gross_Total")]
    open_days = sum(r.get("Status") == "Open" for r in sales)
    closed_days = sum(r.get("Status") == "Closed" for r in sales)
    summary = {"sales": values[0], "expenses": values[1], "operational_expenses": expense_totals["Operational"], "grocery_expenses": expense_totals["Grocery"], "other_expenses": expense_totals["Other"], "drawings": expense_totals["Drawings"], "cash_outflow": expense_totals["Cash_Outflow_Total"], "rent": values[2], "gross_payroll": values[3], "npf": _total(runs, "NPF_Total"), "acc": _total(runs, "ACC_Total"), "net_payroll": _total(runs, "Net_Total"), "operating_result": operating_result(*values), "open_days": open_days, "closed_days": closed_days, "average_sales": values[0] / open_days if open_days else 0}
    includes_startup = lo <= "2025-12-01" and hi >= "2026-02-14"
    if includes_startup:
        summary.update({"startup_costs":startup["Costs"],"other_startup_costs":startup.get("Non_Rent_Costs",startup["Costs"]-startup.get("Rent",0)),"startup_rent":startup.get("Rent",0),"startup_income":startup["Income"],"estimated_cash_position":estimated_cash_position(summary["operating_result"],startup["Costs"],startup["Income"],summary["drawings"])})

    metrics = [("Sales",summary["sales"]),("Operating expenses",summary["expenses"]),("Owner drawings",summary["drawings"]),("Rent after startup",summary["rent"]),("Gross payroll",summary["gross_payroll"]),("Estimated P&L",summary["operating_result"]),("NPF",summary["npf"]),("ACC",summary["acc"]),("Net payroll",summary["net_payroll"])]
    if includes_startup: metrics += [("Other startup costs",summary["other_startup_costs"]),("Startup rent (Dec & Jan)",summary["startup_rent"]),("Startup income",summary["startup_income"]),("Estimated cash position",summary["estimated_cash_position"])]
    for column,(label,value) in zip(st.columns(3)*((len(metrics)+2)//3),metrics): column.metric(label,money(value))
    st.caption(f'Expense categories: Operational {money(summary["operational_expenses"])} · Grocery {money(summary["grocery_expenses"])} · Other {money(summary["other_expenses"])} · Drawings {money(summary["drawings"])} (excluded from estimated P&L)')
    st.caption(f'Inclusive period: {lo} to {hi} · Open days: {open_days} · Closed days: {closed_days} · Average open-day sales: {money(summary["average_sales"])}')
    if not includes_startup: st.caption("Startup costs and startup income appear only when the selected range covers the complete startup period from December 2025 through 14 February 2026.")
    st.info(f'Data included: {len(sales)} sales days · {len(expenses)} expense days · {len(rent)} rent payments · {len(runs)} finalized payroll runs · {len(details)} employee payroll lines')

    st.subheader("Preview selected records")
    tabs = st.tabs(["Sales","Expenses","Rent","Payroll"])
    previews = [sales,expenses,rent,_payroll_export(runs,details)]
    for tab,rows in zip(tabs,previews):
        with tab:
            if rows: st.dataframe(pd.DataFrame(rows),width="stretch",hide_index=True)
            else: st.caption("No matching records in this period.")

    payroll_rows = _payroll_export(runs, details)
    contribution_rows = [{k:r.get(k) for k in ("Payroll_ID","Pay_Date","Employee_ID","Employee_Name","Gross_Pay","NPF_Rate","NPF_Amount","ACC_Rate","ACC_Amount","Net_Pay")} for r in payroll_rows]
    export_data = {**selected,"Payroll_Employee_Lines":payroll_rows,"NPF_ACC":contribution_rows}
    if includes_startup: export_data["Startup"]=[startup]
    stem = f"waterfront_{lo}_to_{hi}"
    st.subheader("Download selected timeframe")
    c1,c2,c3=st.columns(3)
    c1.download_button("Sales CSV",csv_bytes(sales),f"{stem}_sales.csv","text/csv",width="stretch")
    c2.download_button("Expenses CSV",csv_bytes(expenses),f"{stem}_expenses.csv","text/csv",width="stretch")
    c3.download_button("Rent CSV",csv_bytes(rent),f"{stem}_rent.csv","text/csv",width="stretch")
    c4,c5,c6=st.columns(3)
    c4.download_button("Payroll CSV",csv_bytes(payroll_rows),f"{stem}_payroll.csv","text/csv",width="stretch")
    c5.download_button("NPF & ACC CSV",csv_bytes(contribution_rows),f"{stem}_npf_acc.csv","text/csv",width="stretch")
    c6.download_button("Summary PDF",financial_report_pdf(summary,(lo,hi)),f"{stem}_summary.pdf","application/pdf",width="stretch")
    d1,d2=st.columns(2)
    d1.download_button("Complete Excel workbook",excel_bytes(export_data),f"{stem}.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",width="stretch")
    d2.download_button("Complete ZIP backup",complete_backup(export_data),f"{stem}.zip","application/zip",width="stretch")

