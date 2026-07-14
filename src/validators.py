from datetime import datetime
from decimal import Decimal, InvalidOperation
from dateutil import parser

class ValidationError(ValueError): pass
def parse_decimal(value, field="Amount", nonnegative=True):
    try: result=Decimal(str(value))
    except (InvalidOperation, ValueError): raise ValidationError(f"{field} must be a number.")
    if nonnegative and result < 0: raise ValidationError(f"{field} cannot be negative.")
    return result
def parse_date(value):
    if hasattr(value,"isoformat") and not isinstance(value,str): return value.isoformat()
    try: return parser.parse(str(value), dayfirst=True).date().isoformat()
    except (ValueError, TypeError): raise ValidationError("Invalid date.")
def validate_sales(status, amount):
    if status not in ("Open","Closed"): raise ValidationError("Status must be Open or Closed.")
    amount=parse_decimal(amount,"Sales amount")
    return Decimal("0") if status=="Closed" else amount
def validate_period(start,end):
    s=parse_date(start); e=parse_date(end)
    if s>e: raise ValidationError("Period start must not be after period end.")
    return s,e
def validate_month(value):
    try: return datetime.strptime(str(value),"%Y-%m").strftime("%Y-%m")
    except ValueError: raise ValidationError("Rent month must use YYYY-MM.")
