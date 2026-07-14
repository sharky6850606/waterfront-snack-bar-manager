import streamlit as st
from src.auth import logout,require_login
from src.config import APP_NAME,LOGO_PATH
from src.sheets_client import get_workbook,ensure_application_sheets,clear_caches
from src.ui_components import inject_css
from src.pages import dashboard,sales,expenses,rent,employees,payroll,reports,audit_history

st.set_page_config(page_title=APP_NAME,layout="wide",initial_sidebar_state="expanded")
inject_css()
require_login()
if LOGO_PATH.exists(): st.sidebar.image(str(LOGO_PATH),width=118)
st.sidebar.title("Waterfront Snack Bar")
st.sidebar.caption("Financial Manager · Samoa")
pages={"Overview":dashboard.render,"Daily Sales":sales.render,"Daily Expenses":expenses.render,"Rent":rent.render,"Employees":employees.render,"Payroll":payroll.render,"Reports":reports.render,"Activity History":audit_history.render}
page=st.sidebar.radio("Navigation",list(pages),label_visibility="collapsed")
st.sidebar.divider()
if st.sidebar.button("Log out",width="stretch"): logout()
if st.sidebar.button("↻  Refresh data",width="stretch"): clear_caches(); st.cache_data.clear(); st.rerun()
try:
 wb=get_workbook(); st.sidebar.success("Google Sheets connected")
 with st.sidebar.expander("System setup"):
  st.caption("Application sheets are already configured. Use only if a sheet is missing.")
  if st.button("Check application sheets",width="stretch"):
   created=ensure_application_sheets(wb); st.success("Created: "+", ".join(created) if created else "All application sheets are ready")
 pages[page]()
except Exception as exc:
 st.sidebar.error("Not connected")
 st.title(APP_NAME); st.error(str(exc)); st.info("Add .streamlit/secrets.toml using the example file, share the spreadsheet with the service account, then restart the app. No live data was changed.")
