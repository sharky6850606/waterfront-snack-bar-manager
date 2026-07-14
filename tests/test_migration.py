from src.migration import migrate_sales,migrate_payroll,deterministic_id
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
