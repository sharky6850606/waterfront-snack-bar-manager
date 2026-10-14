from src.migration import migrate_sales,migrate_payroll,migrate_startup,deterministic_id
def test_sales_migration():
 rows=[["title"],["Date","Sales"],["31/03/26","100.50"],["01/04/26","Closed"],["Total","100.50"]]; out=migrate_sales(rows); assert len(out)==2; assert out[0]["Date"]=="2026-03-31"; assert out[1]["Sales_Amount"]==0
def test_ids_stable(): assert deterministic_id("X",1)==deterministic_id("X",1)
def test_repeated_payroll_blocks():
 rows=[["Pay Period","01/03/26","07/03/26","08/03/26"],["Employee","Hours","Hourly Rate","Gross Pay","NPF","ACC","Net Pay"],["Clarence","40","7.5","300","30","3","267"],["Totals","","","300","30","3","267"],["Pay Period","08/03/26","14/03/26","15/03/26"],["Employee","Gross Pay","NPF","ACC","Net Pay"],["Hayley","200","20","2","178"]]
 runs,details=migrate_payroll(rows); assert len(runs)==2; assert len(details)==2; assert details[0]["Employee_Name"]=="Clarence"
def test_real_payroll_title_style():
 rows=[["Payroll (2026/07/10)"],["Employee Name","Working Hours","Normal Rate (Tala)","Sunday","Gross Pay","NPF (10%)","ACC (1%)","Net Pay"],["Clarence","40","7.5","0","300","30","3","267"],["Totals","40","7.5","0","300","30","3","267"]]
 runs,details=migrate_payroll(rows); assert len(runs)==1; assert runs[0]["Pay_Date"]=="2026-07-10"; assert len(details)==1
def test_expense_real_headers():
 from src.migration import migrate_expenses
 out=migrate_expenses([["Date","Total Shopping","Total Cash Used","Leftover Change","PDF Link (Breakdown)"],["11/03/2026","598.4","668.8","70.4","PDF File"]]); assert out[0]["Cash_Provided"]==668.8; assert out[0]["Change_Returned"]==70.4
def test_blank_legacy_rows_are_not_counted():
 from src.migration import migrate_expenses,migrate_rent
 assert migrate_sales([["Date","Sales"],["30/06/26",""]])==[]
 assert migrate_expenses([["Date","Total Shopping"],["30/06/26",""]])==[]
 assert migrate_rent([["Date","Month","Amount"],["30/06/26","June",""]])==[]
def test_payroll_marker_is_preserved_without_changing_recorded_expense():
 from src.migration import migrate_expenses
 out=migrate_expenses([["Date","Total Shopping","Total Cash Used","Leftover Change","PDF Link (Breakdown)"],["05/06/26","450","600","150","Payroll"]])
 assert out[0]["Category"]=="Grocery"; assert "marked Payroll" in out[0]["Notes"]
def test_startup_totals_and_corrected_rent_coverage():
 out=migrate_startup([["Item","Amount (T)","Category"],["Rent (legacy label)","2,230.00 T","Rent"],["TOTAL STARTUP COSTS","10,152.77 T",""] ,["TOTAL INCOME","900.00 T",""]])
 assert out["Net"]==-9282.77; assert out["Rent"]==2260; assert out["Recorded_Rent"]==2230; assert out["Non_Rent_Costs"]==7922.77; assert out["Costs"]==10182.77; assert out["Rent_Coverage"]==["2025-11","2025-12"]

