from src.pdf_generator import payslip_pdf,financial_report_pdf
def test_pdf():
 d={"Employee_Name":"Clarence","Normal_Hours":40,"Hourly_Rate":7.5,"Gross_Pay":300,"NPF_Rate":.1,"NPF_Amount":30,"ACC_Rate":.01,"ACC_Amount":3,"Net_Pay":267}; r={"Period_Start":"2026-01-01","Period_End":"2026-01-07","Pay_Date":"2026-01-08"}; assert payslip_pdf(d,r).startswith(b"%PDF")
def test_financial_report_pdf():
 s={"sales":100,"expenses":20,"rent":10,"gross_payroll":30,"npf":3,"acc":.3,"net_payroll":26.7,"operating_result":40,"open_days":1,"closed_days":0,"average_sales":100}; assert financial_report_pdf(s,("2026-06-01","2026-06-30")).startswith(b"%PDF")
