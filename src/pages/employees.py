import streamlit as st
from uuid import uuid4
from ..repositories import EmployeeRepository,PayrollDetailRepository
from ..audit import log_action
from ..ui_components import history_table,guarded_load,page_header

def render():
 page_header("Employees","Manage pay rates, contribution rates, and active team members."); repo=EmployeeRepository(); rows=guarded_load(repo); names=["Add new employee"]+[r["Employee_Name"] for r in rows]; choice=st.selectbox("Employee",names); old=next((r for r in rows if r["Employee_Name"]==choice),None)
 with st.form("employee_form"):
  name=st.text_input("Employee name",value=str(old["Employee_Name"] if old else "")); rate=st.number_input("Hourly rate",min_value=0.0,value=float(old["Hourly_Rate"] if old else 0)); npf=st.number_input("NPF rate",min_value=0.0,max_value=1.0,value=float(old["NPF_Rate"] if old else .10)); acc=st.number_input("ACC rate",min_value=0.0,max_value=1.0,value=float(old["ACC_Rate"] if old else .01)); active=st.checkbox("Active",value=str(old["Active"]).upper()=="TRUE" if old else True); save=st.form_submit_button("Save employee",width="stretch")
 if save:
  try:
   data={"Employee_Name":name.strip(),"Hourly_Rate":rate,"NPF_Rate":npf,"ACC_Rate":acc,"Active":"TRUE" if active else "FALSE"}
   if not data["Employee_Name"]: raise ValueError("Employee name is required.")
   if old: rid=old["Employee_ID"]; repo.update(rid,data); action="UPDATE"
   else: rid=uuid4().hex; repo.append({"Employee_ID":rid,**data}); action="CREATE"
   log_action("Employees",action,rid,f"Saved employee {name}"); st.success("Employee saved."); st.rerun()
  except Exception as e: st.error(str(e))
 if old:
  try: used=any(str(d["Employee_ID"])==str(old["Employee_ID"]) for d in PayrollDetailRepository().all())
  except Exception: used=True
  if used: st.info("This employee has payroll history and cannot be permanently deleted. You can deactivate them.")
  else:
   confirm_delete=st.checkbox("I confirm permanent deletion of this unused employee")
   if st.button("Delete unused employee",disabled=not confirm_delete,width="stretch"):
    try:
     repo.delete(old["Employee_ID"]); log_action("Employees","DELETE",old["Employee_ID"],f'Deleted unused employee {old["Employee_Name"]}'); st.success("Employee deleted."); st.rerun()
    except Exception as e: st.error(str(e))
 st.caption("Employees used in payroll are retained; deactivate them instead of deleting."); history_table(rows,"employees")
