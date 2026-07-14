import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.sheets_client import get_workbook,ensure_application_sheets
from src.repositories import SalesRepository,ExpensesRepository,RentRepository,PayrollRunRepository,PayrollDetailRepository
from src.migration import migrate_sales,migrate_expenses,migrate_rent,migrate_payroll,backup_workbook
from src.audit import log_action

def main():
 p=argparse.ArgumentParser(); p.add_argument("--dry-run",action="store_true"); p.add_argument("--apply",action="store_true"); args=p.parse_args(); wb=get_workbook(); mappings=[("Daily Sales",migrate_sales,SalesRepository),("Daily Expenses",migrate_expenses,ExpensesRepository),("Rent",migrate_rent,RentRepository)]; parsed={}; worksheets={ws.title.strip():ws for ws in wb.worksheets()}
 for name,func,_ in mappings:
  try: parsed[name]=func(worksheets[name].get_all_values())
  except Exception as exc: parsed[name]=[]
 try: payroll_runs,payroll_details=migrate_payroll(worksheets["Payroll"].get_all_values())
 except Exception: payroll_runs,payroll_details=[],[]
 report={"mode":"apply" if args.apply else "dry-run","counts":{**{k:len(v) for k,v in parsed.items()},"Payroll_Runs":len(payroll_runs),"Payroll_Details":len(payroll_details)},"warnings":["Payroll parsing is conservative. Review every detected run and rate before apply; unrecognized blocks are skipped."]}
 if args.apply:
  folder=backup_workbook(wb); report["backup"]=str(folder); ensure_application_sheets(wb)
  for name,_,repo_cls in mappings:
   repo=repo_cls(wb); existing={r[repo.id_field] for r in repo.all()}
   for record in parsed[name]:
    if record[repo.id_field] not in existing: repo.append(record)
  for repo,records in ((PayrollRunRepository(wb),payroll_runs),(PayrollDetailRepository(wb),payroll_details)):
   existing={str(r[repo.id_field]) for r in repo.all()}
   for record in records:
    if str(record[repo.id_field]) not in existing: repo.append(record)
  log_action("Migration","MIGRATE","legacy-v1",json.dumps(report["counts"]),wb)
 out=Path("migration_report.json"); out.write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps(report,indent=2))
if __name__=="__main__": main()
