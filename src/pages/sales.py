import streamlit as st
from datetime import date as date_type
from uuid import uuid4
from ..repositories import SalesRepository
from ..validators import validate_sales
from ..config import now,timestamp
from ..audit import log_action
from ..ui_components import history_table,guarded_load,page_header

def render():
 page_header("Daily Sales","Record open and closed days, update daily takings, and manage sales history."); repo=SalesRepository(); rows=guarded_load(repo)
 if "sales_edit_date" in st.session_state: st.session_state["sales_date"]=st.session_state.pop("sales_edit_date")
 selected=st.date_input("Date",now().date(),key="sales_date"); date=selected.isoformat(); old=next((r for r in rows if r["Date"]==date),None)
 with st.form("sales_form"):
  status=st.radio("Status",["Open","Closed"],index=1 if old and old["Status"]=="Closed" else 0,horizontal=True); amount=st.number_input("Total sales",min_value=0.0,value=float(old["Sales_Amount"] if old else 0),disabled=status=="Closed"); notes=st.text_area("Notes",value=str(old["Notes"] if old else "")); save=st.form_submit_button("Update sale" if old else "Save sale",width="stretch")
 if save:
  try:
   value=validate_sales(status,amount); data={"Date":date,"Status":status,"Sales_Amount":value,"Notes":notes}
   if old: repo.update(old["Sale_ID"],data); action="UPDATE"; rid=old["Sale_ID"]
   else: rid=uuid4().hex; repo.append({"Sale_ID":rid,**data}); action="CREATE"
   log_action("Daily Sales",action,rid,f"{status} sales for {date}"); st.success("Sales record saved."); st.rerun()
  except Exception as e: st.error(str(e))
 st.subheader("Sales history"); history_table(rows,"sales")
 if rows:
  st.subheader("Manage sales entries")
  for record in sorted(rows,key=lambda r:str(r["Date"]),reverse=True):
   with st.container(border=True):
    info,edit_col,delete_col=st.columns([5,1,1]); info.write(f'**{record["Date"]}** · {record["Status"]} · WST ${float(record["Sales_Amount"] or 0):,.2f}')
    if edit_col.button("Edit",key=f'sale_edit_{record["Sale_ID"]}'):
     st.session_state["sales_edit_date"]=date_type.fromisoformat(str(record["Date"])); st.rerun()
    if delete_col.button("Delete",key=f'sale_delete_{record["Sale_ID"]}'): st.session_state["pending_sale_delete"]=record["Sale_ID"]; st.rerun()
    if st.session_state.get("pending_sale_delete")==record["Sale_ID"]:
     st.warning("Delete this sales entry permanently?"); yes,no=st.columns(2)
     if yes.button("Yes, delete",key=f'sale_yes_{record["Sale_ID"]}'):
      repo.delete(record["Sale_ID"]); log_action("Daily Sales","DELETE",record["Sale_ID"],f'Deleted sales for {record["Date"]}'); st.session_state.pop("pending_sale_delete",None); st.rerun()
     if no.button("Cancel",key=f'sale_no_{record["Sale_ID"]}'): st.session_state.pop("pending_sale_delete",None); st.rerun()
