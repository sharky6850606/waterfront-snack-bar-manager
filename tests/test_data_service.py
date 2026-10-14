import pytest

from src.data_service import expense_breakdown, filter_financial_data, include_january_2026_rent, merge_records, normalize_expense_category


def sample_data():
    return {
        "Sales": [{"Date":"2026-06-01","Status":"Open","Sales_Amount":100},{"Date":"2026-07-01","Status":"Open","Sales_Amount":200}],
        "Expenses": [{"Date":"2026-06-02","Total_Shopping":25}],
        "Rent": [{"Rent_ID":"r1","Payment_Date":"2026-06-03","Amount":50}],
        "Payroll_Runs": [{"Payroll_ID":"p1","Pay_Date":"2026-06-04","Status":"Finalized","Gross_Total":80},{"Payroll_ID":"p2","Pay_Date":"2026-06-05","Status":"Voided","Gross_Total":90}],
        "Payroll_Details": [{"Payroll_Detail_ID":"d1","Payroll_ID":"p1"},{"Payroll_Detail_ID":"d2","Payroll_ID":"p2"}],
        "Employees": [{"Employee_ID":"e1"}], "Audit_Log": [{"Timestamp":"2026-06-05T12:00:00+13:00"}],
    }


def test_application_record_overrides_legacy_date():
    rows=merge_records([{"Date":"2026-06-01","Sales_Amount":10}],[{"Date":"2026-06-01","Sales_Amount":20}],"Date")
    assert rows==[{"Date":"2026-06-01","Sales_Amount":20}]


def test_missing_january_2026_rent_is_added_once():
    rows=include_january_2026_rent([])
    assert rows[0]["Rent_For_Month"]=="2026-01"
    assert rows[0]["Amount"]==1130
    assert include_january_2026_rent(rows)==rows


def test_filter_is_inclusive_and_links_only_finalized_payroll_details():
    result=filter_financial_data(sample_data(),"2026-06-01","2026-06-30")
    assert len(result["Sales"])==1
    assert [r["Payroll_ID"] for r in result["Payroll_Runs"]]==["p1"]
    assert [r["Payroll_Detail_ID"] for r in result["Payroll_Details"]]==["d1"]


def test_filter_rejects_reversed_range():
    with pytest.raises(ValueError): filter_financial_data(sample_data(),"2026-07-01","2026-06-01")


def test_legacy_expense_without_category_defaults_to_grocery():
    assert normalize_expense_category("") == "Grocery"


def test_expense_breakdown_excludes_drawings_from_operating_total():
    totals=expense_breakdown([
        {"Category":"Operational","Total_Shopping":100},
        {"Category":"Grocery","Total_Shopping":50},
        {"Category":"Drawings","Total_Shopping":30},
        {"Category":"Other","Total_Shopping":20},
    ])
    assert totals["Operating_Total"] == 170
    assert totals["Cash_Outflow_Total"] == 200

