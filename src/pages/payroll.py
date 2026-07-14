from uuid import uuid4

import streamlit as st

from ..audit import log_action
from ..calculations import payroll_line, payroll_totals
from ..config import now
from ..exports import zip_bytes
from ..pdf_generator import combined_payslips_pdf, payroll_summary_pdf, payslip_pdf
from ..repositories import EmployeeRepository, PayrollDetailRepository, PayrollRunRepository
from ..ui_components import guarded_load, page_header
from ..validators import validate_period


def _finalize(run, details):
    runs, detail_repo, rid = PayrollRunRepository(), PayrollDetailRepository(), run["Payroll_ID"]
    runs.append({**run, "Status": "Processing"})
    try:
        for detail in details:
            detail_repo.append(detail)
        written = [d for d in detail_repo.all() if d["Payroll_ID"] == rid]
        if len(written) != len(details):
            raise RuntimeError("Payroll detail verification failed.")
        totals = payroll_totals(written)
        runs.update(rid, {"Status": "Finalized", "Gross_Total": totals["Gross_Pay"], "NPF_Total": totals["NPF_Amount"], "ACC_Total": totals["ACC_Amount"], "Net_Total": totals["Net_Pay"], "PDF_File_Name": f"payroll_{rid}.pdf"})
        log_action("Payroll", "FINALIZE", rid, f"Finalized payroll with {len(details)} employees")
    except Exception as exc:
        try:
            runs.update(rid, {"Status": "Failed"})
        except Exception:
            pass
        raise RuntimeError(f"Payroll was not finalized. Partial writes may exist for {rid}. {exc}") from exc


def _create_payroll(employees):
    st.subheader("Step 1 — Pay period")
    c1, c2, c3 = st.columns(3)
    start, end, paydate = c1.date_input("Period start"), c2.date_input("Period end"), c3.date_input("Pay date", now().date())
    notes = st.text_area("Notes")
    st.subheader("Step 2 — Employee hours")
    st.caption("Leave optional hours at zero. Overtime is 1.5× and public-holiday work is 2× the normal hourly rate.")
    lines = []
    for employee in employees:
        with st.container(border=True):
            st.markdown(f'#### {employee["Employee_Name"]}')
            c1, c2, c3 = st.columns(3)
            normal = c1.number_input("Normal hours", min_value=0.0, key=f'h_{employee["Employee_ID"]}')
            overtime = c2.number_input("Overtime hours (1.5×)", min_value=0.0, key=f'ot_{employee["Employee_ID"]}')
            holiday = c3.number_input("Public holiday hours (2×)", min_value=0.0, key=f'ph_{employee["Employee_ID"]}')
            calc = payroll_line(normal, employee["Hourly_Rate"], employee["NPF_Rate"], employee["ACC_Rate"], overtime, holiday)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Normal pay", f'WST ${float(calc["Normal_Pay"]):,.2f}')
            m2.metric("Extra pay", f'WST ${float(calc["Overtime_Pay"] + calc["Public_Holiday_Pay"]):,.2f}')
            m3.metric("Gross pay", f'WST ${float(calc["Gross_Pay"]):,.2f}')
            m4.metric("Net pay", f'WST ${float(calc["Net_Pay"]):,.2f}')
            st.caption(f'NPF WST ${float(calc["NPF_Amount"]):,.2f} · ACC WST ${float(calc["ACC_Amount"]):,.2f}')
            lines.append((employee, calc))
    st.subheader("Step 3 — Review and finalize")
    confirm = st.checkbox("I have reviewed the calculations and confirm finalization")
    if st.button("Finalize payroll", disabled=not confirm or not employees, width="stretch"):
        try:
            period_start, period_end = validate_period(start, end)
            rid = uuid4().hex
            run = {"Payroll_ID": rid, "Period_Start": period_start, "Period_End": period_end, "Pay_Date": paydate.isoformat(), "Notes": notes}
            details = [{"Payroll_Detail_ID": uuid4().hex, "Payroll_ID": rid, "Employee_ID": employee["Employee_ID"], "Employee_Name": employee["Employee_Name"], **calc} for employee, calc in lines]
            _finalize(run, details)
            st.success("Payroll finalized.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _finalized_payroll(runs, details_all):
    finalized = [r for r in runs if r["Status"] == "Finalized"]
    if not finalized:
        st.info("No finalized payroll runs yet.")
        return
    st.caption("Use the buttons on each run. Voiding preserves its history and allows a corrected replacement payroll.")
    for run in sorted(finalized, key=lambda r: str(r["Pay_Date"]), reverse=True):
        rid = run["Payroll_ID"]
        details = [d for d in details_all if d["Payroll_ID"] == rid]
        with st.container(border=True):
            st.markdown(f'### Pay date {run["Pay_Date"]}')
            st.caption(f'{run["Period_Start"]} to {run["Period_End"]} · {len(details)} employees · Finalized')
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Gross", f'WST ${float(run["Gross_Total"] or 0):,.2f}')
            m2.metric("NPF", f'WST ${float(run["NPF_Total"] or 0):,.2f}')
            m3.metric("ACC", f'WST ${float(run["ACC_Total"] or 0):,.2f}')
            m4.metric("Net", f'WST ${float(run["Net_Total"] or 0):,.2f}')
            view_col, void_col = st.columns(2)
            viewing = st.session_state.get("payroll_view_id") == rid
            if view_col.button("Hide details" if viewing else "View details & downloads", key=f'payroll_view_{rid}', width="stretch"):
                if viewing:
                    st.session_state.pop("payroll_view_id", None)
                else:
                    st.session_state["payroll_view_id"] = rid
                st.rerun()
            if void_col.button("Void payroll", key=f'payroll_void_{rid}', width="stretch"):
                st.session_state["pending_payroll_void"] = rid
                st.rerun()
            if viewing:
                st.dataframe(details, width="stretch", hide_index=True)
                d1, d2, d3 = st.columns(3)
                d1.download_button("Combined payslips PDF", combined_payslips_pdf(details, run), f'combined_payslips_{run["Pay_Date"]}.pdf', "application/pdf", key=f'combined_{rid}')
                d2.download_button("Payroll summary PDF", payroll_summary_pdf(details, run), f'payroll_summary_{run["Pay_Date"]}.pdf', "application/pdf", key=f'summary_{rid}')
                individual = {f'{d["Employee_Name"]}_payslip.pdf': payslip_pdf(d, run) for d in details}
                d3.download_button("Individual payslips ZIP", zip_bytes(individual), f'payslips_{run["Pay_Date"]}.zip', "application/zip", key=f'zip_{rid}')
            if st.session_state.get("pending_payroll_void") == rid:
                st.warning("Void this finalized payroll? It will remain in history and cannot be edited.")
                yes, no = st.columns(2)
                if yes.button("Yes, void payroll", key=f'void_yes_{rid}', width="stretch"):
                    PayrollRunRepository().update(rid, {"Status": "Voided"})
                    log_action("Payroll", "VOID", rid, "Voided finalized payroll")
                    st.session_state.pop("pending_payroll_void", None)
                    st.session_state.pop("payroll_view_id", None)
                    st.rerun()
                if no.button("Cancel", key=f'void_no_{rid}', width="stretch"):
                    st.session_state.pop("pending_payroll_void", None)
                    st.rerun()


def render():
    page_header("Payroll","Prepare, review, finalize, download, and safely void employee payroll runs.")
    employees = [e for e in guarded_load(EmployeeRepository()) if str(e["Active"]).upper() == "TRUE"]
    runs = guarded_load(PayrollRunRepository())
    details = guarded_load(PayrollDetailRepository())
    create_tab, finalized_tab = st.tabs(["Create payroll", "Finalized payroll"])
    with create_tab:
        _create_payroll(employees)
    with finalized_tab:
        _finalized_payroll(runs, details)
