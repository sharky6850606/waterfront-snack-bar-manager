import streamlit as st
import gspread
from gspread.utils import numericise
from google.oauth2.service_account import Credentials
from .config import DEFAULT_SPREADSHEET_ID, SHEETS, SETTINGS, timestamp

class SheetsConnectionError(RuntimeError): pass

@st.cache_resource(show_spinner=False)
def get_gspread_client():
    try:
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info.get("private_key", "").replace("\\n", "\n")
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        return gspread.authorize(creds)
    except Exception as exc:
        raise SheetsConnectionError("Google Sheets credentials are missing or invalid. Configure .streamlit/secrets.toml.") from exc

@st.cache_resource(show_spinner=False)
def get_workbook():
    try:
        sid = st.secrets.get("SPREADSHEET_ID", DEFAULT_SPREADSHEET_ID)
        return get_gspread_client().open_by_key(sid)
    except SheetsConnectionError: raise
    except Exception as exc: raise SheetsConnectionError("Could not open the configured spreadsheet. Check sharing and spreadsheet ID.") from exc

@st.cache_data(ttl=120,show_spinner=False)
def get_sheet_records(sheet_name):
    """Read and validate one application sheet in one API value request."""
    try:
        values=get_workbook().worksheet(sheet_name).get_all_values()
        expected=SHEETS[sheet_name]
        actual=values[0] if values else []
        if actual[:len(expected)] != expected:
            raise SheetsConnectionError(f"{sheet_name} headers do not match the application schema.")
        records=[]
        for row in values[1:]:
            padded=row+[""]*(len(expected)-len(row))
            records.append({h:(v if i==0 else numericise(v)) for i,(h,v) in enumerate(zip(expected,padded))})
        return records
    except SheetsConnectionError: raise
    except Exception as exc: raise SheetsConnectionError(f"Could not read {sheet_name}. Please wait a minute and refresh.") from exc

def ensure_application_sheets(workbook=None):
    """Create only missing application sheets; never modifies legacy sheets."""
    wb = workbook or get_workbook()
    existing = {ws.title for ws in wb.worksheets()}
    created = []
    for name, headers in SHEETS.items():
        if name not in existing:
            ws = wb.add_worksheet(title=name, rows=1000, cols=max(20, len(headers)))
            ws.update("A1", [headers])
            if name == "App_Settings": ws.update("A2", SETTINGS)
            created.append(name)
    if "Employees" in created:
        ws = wb.worksheet("Employees"); now = timestamp()
        ws.append_rows([
          ["EMP-CLARENCE","Clarence",7.5,0.10,0.01,"TRUE",now,now],
          ["EMP-HAYLEY","Hayley",5.0,0.10,0.01,"TRUE",now,now]])
    # Schema v2 only appends payroll fields; existing finalized values remain in place.
    if "Payroll_Details" in existing:
        ws=wb.worksheet("Payroll_Details"); old=["Payroll_Detail_ID","Payroll_ID","Employee_ID","Employee_Name","Normal_Hours","Hourly_Rate","Gross_Pay","NPF_Rate","NPF_Amount","ACC_Rate","ACC_Amount","Net_Pay","Created_At"]
        if ws.row_values(1)==old: ws.update("A1",[SHEETS["Payroll_Details"]])
    # Schema v3 appends Category without shifting any existing expense value.
    if "Expenses_Data" in existing:
        ws=wb.worksheet("Expenses_Data"); old=["Expense_ID","Date","Total_Shopping","Cash_Provided","Change_Returned","Notes","Created_At","Updated_At"]
        if ws.row_values(1)==old: ws.update("A1",[SHEETS["Expenses_Data"]])
    return created

def clear_caches():
    get_gspread_client.clear()
    get_workbook.clear()
    get_sheet_records.clear()
