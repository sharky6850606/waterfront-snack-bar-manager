"""Combined financial datasets shared by dashboard, reports, and exports."""
from .migration import cached_legacy_dashboard_data
from .repositories import (
    AuditRepository, EmployeeRepository, ExpensesRepository, PayrollDetailRepository,
    PayrollRunRepository, RentRepository, SalesRepository,
)

EXPENSE_CATEGORIES=("Operational","Grocery","Drawings","Other")

def normalize_expense_category(value):
    text=str(value or "").strip().title()
    return text if text in EXPENSE_CATEGORIES else "Grocery"

def expense_breakdown(rows):
    totals={category:0.0 for category in EXPENSE_CATEGORIES}
    for row in rows: totals[normalize_expense_category(row.get("Category"))]+=float(row.get("Total_Shopping") or 0)
    totals["Operating_Total"]=totals["Operational"]+totals["Grocery"]+totals["Other"]
    totals["Cash_Outflow_Total"]=totals["Operating_Total"]+totals["Drawings"]
    return totals


def merge_records(legacy_rows, app_rows, key):
    """Merge without double counting; application records win on matching keys."""
    return list({str(row.get(key, "")): row for row in list(legacy_rows) + list(app_rows)}.values())


def combined_financial_data():
    legacy = cached_legacy_dashboard_data()
    return {
        "Sales": merge_records(legacy["sales"], SalesRepository().all(), "Date"),
        "Expenses": [{**row,"Category":normalize_expense_category(row.get("Category"))} for row in merge_records(legacy["expenses"], ExpensesRepository().all(), "Date")],
        "Rent": merge_records(legacy["rent"], RentRepository().all(), "Rent_ID"),
        "Payroll_Runs": merge_records(legacy["payroll"], PayrollRunRepository().all(), "Payroll_ID"),
        "Payroll_Details": merge_records(legacy["payroll_details"], PayrollDetailRepository().all(), "Payroll_Detail_ID"),
        "Startup": legacy.get("startup", {"Costs":0.0,"Income":0.0,"Net":0.0,"Rent":0.0,"Rent_Coverage":[]}),
        "Employees": EmployeeRepository().all(),
        "Audit_Log": AuditRepository().all(),
    }


def filter_financial_data(datasets, start, end):
    """Return a complete, internally consistent dataset for an inclusive date range."""
    lo, hi = str(start), str(end)
    if lo > hi:
        raise ValueError("The From date must not be after the To date.")
    sales = [r for r in datasets["Sales"] if lo <= str(r.get("Date", "")) <= hi]
    expenses = [r for r in datasets["Expenses"] if lo <= str(r.get("Date", "")) <= hi]
    rent = [r for r in datasets["Rent"] if lo <= str(r.get("Payment_Date", "")) <= hi]
    runs = [r for r in datasets["Payroll_Runs"] if lo <= str(r.get("Pay_Date", "")) <= hi and r.get("Status") == "Finalized"]
    payroll_ids = {str(r.get("Payroll_ID")) for r in runs}
    details = [r for r in datasets["Payroll_Details"] if str(r.get("Payroll_ID")) in payroll_ids]
    audit = [r for r in datasets["Audit_Log"] if lo <= str(r.get("Timestamp", ""))[:10] <= hi]
    return {"Sales": sales, "Expenses": expenses, "Rent": rent, "Payroll_Runs": runs, "Payroll_Details": details, "Employees": datasets["Employees"], "Audit_Log": audit}

