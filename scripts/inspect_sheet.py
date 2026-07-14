from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.sheets_client import get_workbook

def main():
    wb=get_workbook()
    for ws in wb.worksheets(): print(f"{ws.title}: {ws.row_count} rows x {ws.col_count} columns")
if __name__=="__main__": main()
