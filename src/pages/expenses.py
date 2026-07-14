import streamlit as st
from datetime import date as date_type
from uuid import uuid4
from ..repositories import ExpensesRepository
from ..validators import parse_decimal
from ..config import now
from ..audit import log_action
from ..ui_components import history_table,guarded_load,page_header
from ..data_service import EXPENSE_CATEGORIES,normalize_expense_category

def render():
 page_header("Daily Expenses","Categorise expenses and record cash provided with automatic change calculation."); repo=ExpensesRepository(); rows=guarded_load(repo)
 if "expense_edit_date" in st.session_state: st.session_state["expense_date"]=st.session_state.pop("expense_edit_date")
 selected=st.date_input("Date",now().date(),key="expense_date"); date=selected.isoformat(); old=next((r for r in rows if r["Date"]==date),None)
 st.caption("Change returned calculates automatically as Cash provided minus Total amount.")
 category_default=normalize_expense_category(old.get("Category") if old else "Grocery"); category=st.selectbox("Category",EXPENSE_CATEGORIES,index=EXPENSE_CATEGORIES.index(category_default),key=f'expense_category_{date}',help="Drawings are owner withdrawals and are excluded from estimated operating profit.")
 total=st.number_input("Total amount",min_value=0.0,value=float(old["Total_Shopping"] if old else 0),key=f'expense_total_{date}'); cash=st.number_input("Cash provided",min_value=0.0,value=float(old["Cash_Provided"] if old else 0),key=f'expense_cash_{date}'); change=cash-total; st.metric("Change returned",f"WST ${change:,.2f}")
 if change<0: st.error("Cash provided cannot be less than the total amount.")
 notes=st.text_area("Notes",value=str(old["Notes"] if old else ""),key=f'expense_notes_{date}'); save=st.button("Update expenses" if old else "Save expenses",width="stretch",disabled=change<0)
 if save:
  try:
   parse_decimal(total,"Total amount"); parse_decimal(cash,"Cash provided"); data={"Date":date,"Total_Shopping":total,"Cash_Provided":cash,"Change_Returned":cash-total,"Notes":notes,"Category":category}
   if old: rid=old["Expense_ID"]; repo.update(rid,data); action="UPDATE"
   else: rid=uuid4().hex; repo.append({"Expense_ID":rid,**data}); action="CREATE"
   log_action("Daily Expenses",action,rid,f"Expenses for {date}"); st.success("Expense record saved."); st.rerun()
  except Exception as e: st.error(str(e))
 st.subheader("Expense history"); history_table(rows,"expenses")
 if rows:
  st.subheader("Manage expense entries")
  for record in sorted(rows,key=lambda r:str(r["Date"]),reverse=True):
   with st.container(border=True):
    info,edit_col,delete_col=st.columns([5,1,1]); info.write(f'**{record["Date"]}** · {normalize_expense_category(record.get("Category"))} · WST ${float(record["Total_Shopping"] or 0):,.2f} · Change WST ${float(record["Change_Returned"] or 0):,.2f}')
    if edit_col.button("Edit",key=f'expense_edit_{record["Expense_ID"]}'):
     st.session_state["expense_edit_date"]=date_type.fromisoformat(str(record["Date"])); st.rerun()
    if delete_col.button("Delete",key=f'expense_delete_{record["Expense_ID"]}'): st.session_state["pending_expense_delete"]=record["Expense_ID"]; st.rerun()
    if st.session_state.get("pending_expense_delete")==record["Expense_ID"]:
     st.warning("Delete this expense entry permanently?"); yes,no=st.columns(2)
     if yes.button("Yes, delete",key=f'expense_yes_{record["Expense_ID"]}'):
      repo.delete(record["Expense_ID"]); log_action("Daily Expenses","DELETE",record["Expense_ID"],f'Deleted expenses for {record["Date"]}'); st.session_state.pop("pending_expense_delete",None); st.rerun()
     if no.button("Cancel",key=f'expense_no_{record["Expense_ID"]}'): st.session_state.pop("pending_expense_delete",None); st.rerun()
