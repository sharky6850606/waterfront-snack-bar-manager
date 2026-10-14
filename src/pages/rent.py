import calendar
from datetime import date
from uuid import uuid4

import streamlit as st

from ..audit import log_action
from ..config import now
from ..repositories import RentRepository
from ..data_service import combined_financial_data
from ..config import money
from ..ui_components import guarded_load, history_table, page_header


def render():
    page_header("Rent","Track monthly rent payments, references, methods, and payment history.")
    repo = RentRepository()
    rows = guarded_load(repo)
    editing_id = st.session_state.get("rent_edit_id")
    editing = next((r for r in rows if str(r["Rent_ID"]) == str(editing_id)), None)
    if editing_id and not editing:
        st.session_state.pop("rent_edit_id", None)

    st.subheader("Edit rent payment" if editing else "Add rent payment")
    record_key = str(editing_id or "new")
    payment_default = date.fromisoformat(str(editing["Payment_Date"])) if editing else now().date()
    rent_month = str(editing["Rent_For_Month"]) if editing else payment_default.strftime("%Y-%m")
    default_year, default_month = map(int, rent_month.split("-"))
    with st.container(border=True):
        payment = st.date_input("Payment date", payment_default, key=f"rent_payment_{record_key}")
        month_col, year_col = st.columns(2)
        month_name = month_col.selectbox("Rent month", list(calendar.month_name)[1:], index=default_month - 1, key=f"rent_month_{record_key}")
        year = year_col.number_input("Rent year", min_value=2020, max_value=2100, value=default_year, step=1, key=f"rent_year_{record_key}")
        month_key = f"{int(year):04d}-{list(calendar.month_name).index(month_name):02d}"
        description = st.text_input("Description", value=str(editing.get("Description", "") if editing else ""), key=f"rent_desc_{record_key}")
        amount = st.number_input("Amount", min_value=0.0, value=float(editing.get("Amount", 0) if editing else 0), key=f"rent_amount_{record_key}")
        methods = ["", "Cash", "Bank Transfer", "Other", "Unknown"]
        old_method = str(editing.get("Payment_Method", "") if editing else "")
        method = st.selectbox("Payment method", methods, index=methods.index(old_method) if old_method in methods else 0, key=f"rent_method_{record_key}")
        reference = st.text_input("Reference", value=str(editing.get("Reference", "") if editing else ""), key=f"rent_ref_{record_key}")
        notes = st.text_area("Notes", value=str(editing.get("Notes", "") if editing else ""), key=f"rent_notes_{record_key}")
        duplicates = [r for r in rows if str(r["Rent_For_Month"]) == month_key and str(r["Rent_ID"]) != str(editing_id)]
        allow = st.checkbox("Allow an additional payment for this month", disabled=not duplicates, key=f"rent_allow_{record_key}")
        if duplicates:
            st.warning(f"A rent payment already exists for {month_name} {int(year)}.")
        save = st.button("Update rent payment" if editing else "Save rent payment", width="stretch")
        cancel = st.button("Cancel edit", width="stretch") if editing else False
    if cancel:
        st.session_state.pop("rent_edit_id", None)
        st.rerun()
    if save:
        if duplicates and not allow:
            st.error("Confirm the additional payment before saving.")
        else:
            try:
                data = {"Payment_Date": payment.isoformat(), "Rent_For_Month": month_key, "Description": description, "Amount": amount, "Payment_Method": method, "Reference": reference, "Notes": notes}
                if editing:
                    rid = editing["Rent_ID"]; repo.update(rid, data); action = "UPDATE"
                else:
                    rid = uuid4().hex; repo.append({"Rent_ID": rid, **data}); action = "CREATE"
                log_action("Rent", action, rid, f"Rent payment for {month_key}")
                st.session_state.pop("rent_edit_id", None)
                st.success("Rent payment saved.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    st.subheader("All recorded rent history")
    datasets=combined_financial_data(); startup=datasets["Startup"]
    startup_row={"Rent_ID":"LEGACY-STARTUP-RENT","Payment_Date":"Before opening","Rent_For_Month":"2025-11 and 2025-12","Description":"Startup rent","Amount":startup.get("Rent",0),"Payment_Method":"Legacy record","Reference":"","Notes":"Included in Startup Expenses; not deducted twice"}
    all_rows=([startup_row] if float(startup.get("Rent") or 0)>0 else [])+datasets["Rent"]
    st.metric("Total rent paid",money(sum(float(row.get("Amount") or 0) for row in all_rows)))
    history_table(all_rows, "all_rent")
    st.caption("November and December 2025 are recorded in Startup Expenses. January 2026 is included as the owner-confirmed historical correction; later months come from the legacy and application rent records.")
    if rows:
        st.subheader("Manage rent entries")
        for record in sorted(rows, key=lambda r: str(r["Payment_Date"]), reverse=True):
            with st.container(border=True):
                info, edit_col, delete_col = st.columns([5, 1, 1])
                info.write(f'**{record["Rent_For_Month"]}** · Paid {record["Payment_Date"]} · WST ${float(record["Amount"] or 0):,.2f}')
                if edit_col.button("Edit", key=f'rent_edit_{record["Rent_ID"]}'):
                    st.session_state["rent_edit_id"] = record["Rent_ID"]
                    st.rerun()
                if delete_col.button("Delete", key=f'rent_delete_{record["Rent_ID"]}'):
                    st.session_state["pending_rent_delete"] = record["Rent_ID"]
                    st.rerun()
                if st.session_state.get("pending_rent_delete") == record["Rent_ID"]:
                    st.warning("Delete this rent entry permanently?")
                    yes, no = st.columns(2)
                    if yes.button("Yes, delete", key=f'rent_yes_{record["Rent_ID"]}'):
                        repo.delete(record["Rent_ID"])
                        log_action("Rent", "DELETE", record["Rent_ID"], f'Deleted rent payment for {record["Rent_For_Month"]}')
                        st.session_state.pop("pending_rent_delete", None)
                        st.rerun()
                    if no.button("Cancel", key=f'rent_no_{record["Rent_ID"]}'):
                        st.session_state.pop("pending_rent_delete", None)
                        st.rerun()

