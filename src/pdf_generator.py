from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from .config import LOGO_PATH, money

RED=colors.HexColor("#E52B2F"); ORANGE=colors.HexColor("#F58220"); BG=colors.HexColor("#F6F3EE")
def _story(detail,run,include_page_break=False):
    styles=getSampleStyleSheet(); title=ParagraphStyle("PayTitle",parent=styles["Title"],alignment=TA_CENTER,textColor=RED)
    story=[]
    if LOGO_PATH.exists(): story.append(Image(str(LOGO_PATH),width=28*mm,height=28*mm))
    story += [Paragraph("Waterfront Snack Bar",title),Paragraph("PAYSLIP",title),Spacer(1,5*mm)]
    story.append(Table([["Employee",detail["Employee_Name"]],["Pay period",f'{run["Period_Start"]} to {run["Period_End"]}'],["Pay date",run["Pay_Date"]]],colWidths=[45*mm,105*mm],style=[("BACKGROUND",(0,0),(0,-1),BG),("GRID",(0,0),(-1,-1),.4,colors.grey),("PADDING",(0,0),(-1,-1),7)]))
    deductions=float(detail["NPF_Amount"])+float(detail["ACC_Amount"])
    rows=[["Description","Rate / Hours","Amount"],["Normal hours",detail["Normal_Hours"],money(detail.get("Normal_Pay",detail["Gross_Pay"]))],["Hourly rate","",money(detail["Hourly_Rate"])]]
    if float(detail.get("Overtime_Hours",0) or 0)>0: rows.append(["Overtime",f'{detail["Overtime_Hours"]} hrs × {money(detail["Overtime_Rate"])}',money(detail["Overtime_Pay"])])
    if float(detail.get("Public_Holiday_Hours",0) or 0)>0: rows.append(["Public holiday",f'{detail["Public_Holiday_Hours"]} hrs × {money(detail["Public_Holiday_Rate"])}',money(detail["Public_Holiday_Pay"])])
    rows += [["Gross pay","",money(detail["Gross_Pay"])],["NPF",f'{float(detail["NPF_Rate"])*100:.2f}%',money(detail["NPF_Amount"])],["ACC",f'{float(detail["ACC_Rate"])*100:.2f}%',money(detail["ACC_Amount"])],["Total deductions","",money(deductions)],["NET PAY","",money(detail["Net_Pay"])]]
    story += [Spacer(1,5*mm),Table(rows,colWidths=[70*mm,35*mm,45*mm],style=[("BACKGROUND",(0,0),(-1,0),ORANGE),("TEXTCOLOR",(0,0),(-1,0),colors.white),("BACKGROUND",(0,-1),(-1,-1),RED),("TEXTCOLOR",(0,-1),(-1,-1),colors.white),("ALIGN",(2,1),(2,-1),"RIGHT"),("GRID",(0,0),(-1,-1),.4,colors.grey),("PADDING",(0,0),(-1,-1),7)])]
    if include_page_break: story.append(PageBreak())
    return story
def payslip_pdf(detail,run):
    out=BytesIO(); SimpleDocTemplate(out,pagesize=A4,rightMargin=20*mm,leftMargin=20*mm).build(_story(detail,run)); return out.getvalue()
def combined_payslips_pdf(details,run):
    out=BytesIO(); story=[]
    for i,d in enumerate(details): story += _story(d,run,i<len(details)-1)
    SimpleDocTemplate(out,pagesize=A4,rightMargin=20*mm,leftMargin=20*mm).build(story); return out.getvalue()
def payroll_summary_pdf(details,run):
    out=BytesIO(); styles=getSampleStyleSheet(); story=[Paragraph("Waterfront Snack Bar",styles["Title"]),Paragraph("Payroll Summary",styles["Heading1"]),Paragraph(f'{run["Period_Start"]} to {run["Period_End"]} — Pay date {run["Pay_Date"]}',styles["Normal"]),Spacer(1,5*mm)]
    rows=[["Employee","Gross","NPF","ACC","Net"]]+[[d["Employee_Name"],money(d["Gross_Pay"]),money(d["NPF_Amount"]),money(d["ACC_Amount"]),money(d["Net_Pay"])] for d in details]
    story.append(Table(rows,repeatRows=1,style=[("BACKGROUND",(0,0),(-1,0),RED),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.grey),("ALIGN",(1,1),(-1,-1),"RIGHT"),("PADDING",(0,0),(-1,-1),6)])); SimpleDocTemplate(out,pagesize=A4).build(story); return out.getvalue()

def financial_report_pdf(summary,period):
    out=BytesIO(); styles=getSampleStyleSheet(); story=[]
    if LOGO_PATH.exists(): story.append(Image(str(LOGO_PATH),width=25*mm,height=25*mm))
    story += [Paragraph("Waterfront Snack Bar",styles["Title"]),Paragraph("Financial Management Report",styles["Heading1"]),Paragraph(f'{period[0]} to {period[1]} · Samoa time',styles["Normal"]),Spacer(1,6*mm)]
    rows=[["Measure","Amount"],["Sales",money(summary["sales"])],["Operational expenses",money(summary.get("operational_expenses",0))],["Grocery expenses",money(summary.get("grocery_expenses",summary.get("expenses",0)))],["Other expenses",money(summary.get("other_expenses",0))],["Operating expense subtotal",money(summary["expenses"])],["Owner drawings (excluded from P&L)",money(summary.get("drawings",0))],["Rent",money(summary["rent"])],["Gross payroll",money(summary["gross_payroll"])],["NPF",money(summary["npf"])],["ACC",money(summary["acc"])],["Net payroll",money(summary["net_payroll"])],["Estimated operating result",money(summary["operating_result"])]]
    story.append(Table(rows,colWidths=[90*mm,65*mm],style=[("BACKGROUND",(0,0),(-1,0),RED),("TEXTCOLOR",(0,0),(-1,0),colors.white),("BACKGROUND",(0,-1),(-1,-1),BG),("GRID",(0,0),(-1,-1),.4,colors.grey),("ALIGN",(1,1),(1,-1),"RIGHT"),("PADDING",(0,0),(-1,-1),8)]))
    story += [Spacer(1,6*mm),Paragraph(f'Open days: {summary["open_days"]} &nbsp;&nbsp; Closed days: {summary["closed_days"]} &nbsp;&nbsp; Average open-day sales: {money(summary["average_sales"])}',styles["Normal"]),Spacer(1,5*mm),Paragraph("Estimated operating result is an internal management estimate and is not audited profit.",styles["Italic"])]
    SimpleDocTemplate(out,pagesize=A4,rightMargin=20*mm,leftMargin=20*mm).build(story); return out.getvalue()
