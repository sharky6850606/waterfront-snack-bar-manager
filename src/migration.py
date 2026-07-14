import csv,json,re,hashlib
import streamlit as st
from datetime import datetime
from pathlib import Path
from .validators import parse_date

def deterministic_id(prefix,*parts): return f"MIG-{prefix}-"+hashlib.sha256("|".join(map(str,parts)).encode()).hexdigest()[:16]
def find_header(rows, required):
    wanted={x.lower() for x in required}
    for i,row in enumerate(rows):
        cells={str(x).strip().lower() for x in row}
        if wanted.issubset(cells): return i
    return None
def _number(value):
    try: return float(re.sub(r"[^0-9.-]","",str(value)))
    except ValueError: return 0.0
def migrate_sales(rows):
    idx=find_header(rows,["date"]); out=[]
    if idx is None: return out
    headers=[str(x).strip().lower() for x in rows[idx]]
    for row in rows[idx+1:]:
        data=dict(zip(headers,row)); raw=data.get("date","")
        if not raw or "total" in str(raw).lower(): continue
        try: date=parse_date(raw)
        except Exception: continue
        joined=" ".join(map(str,row)); status="Closed" if "closed" in joined.lower() else "Open"; amount=0 if status=="Closed" else _number(data.get("sales",data.get("total sales",0)))
        out.append({"Sale_ID":deterministic_id("SALE",date),"Date":date,"Status":status,"Sales_Amount":amount,"Notes":"Migrated from legacy Daily Sales"})
    return out
def migrate_expenses(rows):
    idx=find_header(rows,["date"]); out=[]
    if idx is None:return out
    headers=[str(x).strip().lower() for x in rows[idx]]
    for row in rows[idx+1:]:
        d=dict(zip(headers,row)); raw=d.get("date","")
        if not raw or "total" in str(raw).lower():continue
        try: date=parse_date(raw)
        except Exception:continue
        total=_number(d.get("total shopping",d.get("shopping",0))); cash=_number(d.get("cash provided",d.get("total cash used",d.get("cash",0)))); change=_number(d.get("change returned",d.get("leftover change",cash-total)))
        out.append({"Expense_ID":deterministic_id("EXP",date),"Date":date,"Total_Shopping":total,"Cash_Provided":cash,"Change_Returned":change,"Notes":"Migrated from legacy Daily Expenses","Category":"Grocery"})
    return out
def migrate_rent(rows):
    idx=find_header(rows,["date"]); out=[]
    if idx is None:return out
    headers=[str(x).strip().lower() for x in rows[idx]]
    for n,row in enumerate(rows[idx+1:]):
        d=dict(zip(headers,row)); raw=d.get("date",d.get("payment date",""))
        if not raw or "total" in str(raw).lower():continue
        try: date=parse_date(raw)
        except Exception:continue
        month=str(d.get("rent for month",date[:7]))[:7]
        out.append({"Rent_ID":deterministic_id("RENT",date,month,n),"Payment_Date":date,"Rent_For_Month":month,"Description":d.get("description","Migrated rent"),"Amount":_number(d.get("amount",0)),"Payment_Method":d.get("payment method","Unknown"),"Reference":d.get("reference",""),"Notes":"Migrated from legacy Rent"})
    return out
def migrate_payroll(rows):
    """Conservatively parse repeated payroll tables; unrecognized blocks are skipped."""
    runs=[]; details=[]; current=None; headers=None
    for n,row in enumerate(rows):
        cells=[str(x).strip() for x in row]; low=[x.lower() for x in cells]; joined=" ".join(low)
        if "http" in joined and ("pdf" in joined or "drive" in joined): continue
        payroll_title=re.search(r"payroll\s*\((\d{4})[/-](\d{1,2})[/-](\d{1,2})\)",joined,re.I)
        if "period start" in joined or "pay period" in joined or payroll_title:
            dates=[]
            if payroll_title:
                dates.append(f"{payroll_title.group(1)}-{int(payroll_title.group(2)):02d}-{int(payroll_title.group(3)):02d}")
            for cell in cells:
                try: dates.append(parse_date(cell))
                except Exception: pass
            if dates:
                pay=dates[-1]; end=dates[1] if len(dates)>1 else pay; start=dates[0] if len(dates)>2 else end; pid=deterministic_id("PAY",start,end,pay,n)
                current={"Payroll_ID":pid,"Period_Start":start,"Period_End":end,"Pay_Date":pay,"Status":"Finalized","Notes":"Migrated from legacy Payroll","PDF_File_Name":""}; runs.append(current); headers=None
            continue
        if any(x in low for x in ("employee","employee name","name")) and any("gross" in x for x in low): headers=low; continue
        if not current or not headers or not any(cells) or "total" in joined: continue
        d=dict(zip(headers,cells)); name=d.get("employee",d.get("employee name",d.get("name",""))).strip()
        if not name: continue
        gross=_number(next((v for k,v in d.items() if "gross" in k),0)); npf=_number(next((v for k,v in d.items() if "npf" in k and "rate" not in k),0)); acc=_number(next((v for k,v in d.items() if "acc" in k and "rate" not in k),0)); net=_number(next((v for k,v in d.items() if "net" in k),gross-npf-acc))
        details.append({"Payroll_Detail_ID":deterministic_id("PAYD",current["Payroll_ID"],name),"Payroll_ID":current["Payroll_ID"],"Employee_ID":deterministic_id("EMP",name.lower()),"Employee_Name":name,"Normal_Hours":_number(next((v for k,v in d.items() if "hour" in k and "rate" not in k),0)),"Hourly_Rate":_number(next((v for k,v in d.items() if "hourly" in k or k=="rate"),0)),"Gross_Pay":gross,"NPF_Rate":0,"NPF_Amount":npf,"ACC_Rate":0,"ACC_Amount":acc,"Net_Pay":net})
    valid={d["Payroll_ID"] for d in details}; runs=[r for r in runs if r["Payroll_ID"] in valid]
    for run in runs:
        ds=[d for d in details if d["Payroll_ID"]==run["Payroll_ID"]]; run.update({"Gross_Total":sum(d["Gross_Pay"] for d in ds),"NPF_Total":sum(d["NPF_Amount"] for d in ds),"ACC_Total":sum(d["ACC_Amount"] for d in ds),"Net_Total":sum(d["Net_Pay"] for d in ds)})
    return runs,details

def legacy_dashboard_data(workbook):
    """Batch-read supported legacy tabs for a read-only dashboard preview."""
    by_name={ws.title.strip():ws for ws in workbook.worksheets()}
    sales=migrate_sales(by_name["Daily Sales"].get_all_values()) if "Daily Sales" in by_name else []
    expenses=migrate_expenses(by_name["Daily Expenses"].get_all_values()) if "Daily Expenses" in by_name else []
    rent=migrate_rent(by_name["Rent"].get_all_values()) if "Rent" in by_name else []
    runs,details=migrate_payroll(by_name["Payroll"].get_all_values()) if "Payroll" in by_name else ([],[])
    return {"sales":sales,"expenses":expenses,"rent":rent,"payroll":runs,"payroll_details":details}

@st.cache_data(ttl=300,show_spinner=False)
def cached_legacy_dashboard_data():
    """Cache legacy preview reads to avoid quota use on every Streamlit widget rerun."""
    from .sheets_client import get_workbook
    return legacy_dashboard_data(get_workbook())
def backup_workbook(workbook,root="backups"):
    folder=Path(root)/datetime.now().strftime("%Y%m%d_%H%M%S"); folder.mkdir(parents=True,exist_ok=False); manifest=[]
    try:
        for ws in workbook.worksheets():
            rows=ws.get_all_values(); safe=re.sub(r"[^A-Za-z0-9_-]","_",ws.title); path=folder/f"{safe}.csv"
            with path.open("w",newline="",encoding="utf-8-sig") as f: csv.writer(f).writerows(rows)
            manifest.append({"title":ws.title,"rows":len(rows),"file":path.name})
        (folder/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    except Exception:
        raise RuntimeError(f"Backup failed; migration aborted. Inspect {folder}")
    return folder
