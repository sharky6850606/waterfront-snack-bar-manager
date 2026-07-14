from decimal import Decimal
from uuid import uuid4
from .config import SHEETS, timestamp
from .sheets_client import get_workbook,get_sheet_records

class RepositoryError(RuntimeError): pass
class SheetRepository:
    def __init__(self, sheet_name, id_field, workbook=None):
        self.sheet_name=sheet_name; self.id_field=id_field; self.workbook=workbook
    @property
    def ws(self): return (self.workbook or get_workbook()).worksheet(self.sheet_name)
    def validate_headers(self):
        actual=self.ws.row_values(1); expected=SHEETS[self.sheet_name]
        if actual[:len(expected)] != expected: raise RepositoryError(f"{self.sheet_name} headers do not match the application schema.")
        return True
    def all(self): return get_sheet_records(self.sheet_name)
    def find_by_id(self, record_id): return next((r for r in self.all() if str(r.get(self.id_field))==str(record_id)),None)
    def find_by_date(self, date, field="Date"): return next((r for r in self.all() if str(r.get(field))==str(date)),None)
    def append(self, record):
        get_sheet_records(self.sheet_name); record=dict(record); record.setdefault(self.id_field,uuid4().hex); record.setdefault("Created_At",timestamp()); record.setdefault("Updated_At",record.get("Created_At"))
        self.ws.append_row([self._cell(record.get(h,"")) for h in SHEETS[self.sheet_name]], value_input_option="USER_ENTERED"); get_sheet_records.clear(); return record
    def update(self, record_id, changes):
        rows=self.all(); idx=next((i for i,r in enumerate(rows,2) if str(r.get(self.id_field))==str(record_id)),None)
        if not idx: raise RepositoryError(f"Record {record_id} was not found.")
        merged={**rows[idx-2],**changes,"Updated_At":timestamp()}; self.ws.update(f"A{idx}",[[self._cell(merged.get(h,"")) for h in SHEETS[self.sheet_name]]],value_input_option="USER_ENTERED"); get_sheet_records.clear(); return merged
    def delete(self, record_id):
        rows=self.all(); idx=next((i for i,r in enumerate(rows,2) if str(r.get(self.id_field))==str(record_id)),None)
        if not idx: raise RepositoryError(f"Record {record_id} was not found.")
        self.ws.delete_rows(idx); get_sheet_records.clear()
    @staticmethod
    def _cell(v): return float(v) if isinstance(v,Decimal) else v

class SalesRepository(SheetRepository):
    def __init__(self,workbook=None): super().__init__("Sales_Data","Sale_ID",workbook)
class ExpensesRepository(SheetRepository):
    def __init__(self,workbook=None): super().__init__("Expenses_Data","Expense_ID",workbook)
class RentRepository(SheetRepository):
    def __init__(self,workbook=None): super().__init__("Rent_Data","Rent_ID",workbook)
class EmployeeRepository(SheetRepository):
    def __init__(self,workbook=None): super().__init__("Employees","Employee_ID",workbook)
class PayrollRunRepository(SheetRepository):
    def __init__(self,workbook=None): super().__init__("Payroll_Runs","Payroll_ID",workbook)
class PayrollDetailRepository(SheetRepository):
    def __init__(self,workbook=None): super().__init__("Payroll_Details","Payroll_Detail_ID",workbook)
class AuditRepository(SheetRepository):
    def __init__(self,workbook=None): super().__init__("Audit_Log","Audit_ID",workbook)
