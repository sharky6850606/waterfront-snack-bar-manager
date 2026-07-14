from uuid import uuid4
from .config import timestamp
from .repositories import AuditRepository

ACTIONS={"CREATE","UPDATE","DELETE","INITIALISE","MIGRATE","FINALIZE","VOID","EXPORT"}
def log_action(module,action,record_id,summary,workbook=None):
    if action not in ACTIONS: raise ValueError("Unsupported audit action")
    return AuditRepository(workbook).append({"Audit_ID":uuid4().hex,"Timestamp":timestamp(),"Module":module,"Action":action,"Record_ID":record_id,"Summary":summary})
