from src.exports import csv_bytes,excel_bytes,zip_bytes
def test_exports():
 rows=[{"A":1}]; assert b"A" in csv_bytes(rows); assert excel_bytes({"Data":rows}).startswith(b"PK"); assert zip_bytes({"x.txt":b"x"}).startswith(b"PK")
