from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import pandas as pd

def csv_bytes(records): return pd.DataFrame(records).to_csv(index=False).encode("utf-8-sig")
def excel_bytes(sheets):
    out=BytesIO()
    with pd.ExcelWriter(out,engine="openpyxl") as writer:
        for name,records in sheets.items(): pd.DataFrame(records).to_excel(writer,sheet_name=name[:31],index=False)
    return out.getvalue()
def zip_bytes(files):
    out=BytesIO()
    with ZipFile(out,"w",ZIP_DEFLATED) as z:
        for name,data in files.items(): z.writestr(name,data)
    return out.getvalue()
def complete_backup(datasets, extra_files=None):
    files={f"csv/{name}.csv":csv_bytes(rows) for name,rows in datasets.items()}
    files["waterfront_complete.xlsx"]=excel_bytes(datasets)
    files.update(extra_files or {})
    return zip_bytes(files)
