from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

APP_NAME = "Waterfront Snack Bar Manager"
BUSINESS_NAME = "Waterfront Snack Bar"
DEFAULT_SPREADSHEET_ID = "1oX20BjwHKcvZECa5cDMOkN8iEOalF57AbznvGrynB0M"
TIMEZONE = ZoneInfo("Pacific/Apia")
CURRENCY = "WST"
ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = ROOT / "assets" / "waterfront_logo.png"
BRAND = {"black":"#0B0B0B","red":"#E52B2F","orange":"#F58220","yellow":"#FFC247","white":"#FFFFFF","background":"#F6F3EE","text":"#1C1C1C"}

SHEETS = {
 "App_Settings": ["Key","Value","Description"],
 "Sales_Data": ["Sale_ID","Date","Status","Sales_Amount","Notes","Created_At","Updated_At"],
 "Expenses_Data": ["Expense_ID","Date","Total_Shopping","Cash_Provided","Change_Returned","Notes","Created_At","Updated_At","Category"],
 "Rent_Data": ["Rent_ID","Payment_Date","Rent_For_Month","Description","Amount","Payment_Method","Reference","Notes","Created_At","Updated_At"],
 "Employees": ["Employee_ID","Employee_Name","Hourly_Rate","NPF_Rate","ACC_Rate","Active","Created_At","Updated_At"],
 "Payroll_Runs": ["Payroll_ID","Period_Start","Period_End","Pay_Date","Status","Gross_Total","NPF_Total","ACC_Total","Net_Total","Notes","PDF_File_Name","Created_At","Updated_At"],
 "Payroll_Details": ["Payroll_Detail_ID","Payroll_ID","Employee_ID","Employee_Name","Normal_Hours","Hourly_Rate","Gross_Pay","NPF_Rate","NPF_Amount","ACC_Rate","ACC_Amount","Net_Pay","Created_At","Normal_Pay","Overtime_Hours","Overtime_Rate","Overtime_Pay","Public_Holiday_Hours","Public_Holiday_Rate","Public_Holiday_Pay"],
 "Audit_Log": ["Audit_ID","Timestamp","Module","Action","Record_ID","Summary"],
}
SETTINGS = [
 ["business_name",BUSINESS_NAME,"Business name"],["currency",CURRENCY,"Currency"],["timezone","Pacific/Apia","Business timezone"],
 ["default_npf_rate","0.10","Default NPF rate"],["default_acc_rate","0.01","Default ACC rate"],
 ["spreadsheet_id",DEFAULT_SPREADSHEET_ID,"Spreadsheet ID"],["schema_version","3","Schema version"],
 ["migration_completed","FALSE","Legacy migration status"],["last_migration_at","","Last migration timestamp"]]

def now(): return datetime.now(TIMEZONE)
def timestamp(): return now().isoformat(timespec="seconds")
def money(value): return f"{CURRENCY} ${float(value or 0):,.2f}"
def samoa_datetime(value):
    """Render stored ISO timestamps explicitly in the business timezone."""
    if not value: return ""
    try:
        dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        if dt.tzinfo is None: dt=dt.replace(tzinfo=TIMEZONE)
        return dt.astimezone(TIMEZONE).strftime("%d/%m/%Y %I:%M:%S %p Samoa")
    except (ValueError,TypeError): return str(value)
