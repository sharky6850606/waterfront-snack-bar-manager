# Waterfront Snack Bar Manager

A zero-cost, single-owner Streamlit application for sales, categorised daily expenses, rent, employees, payroll, payslips, reports, activity history, and data exports. Access is protected by a private username and password stored only in Streamlit Secrets. Google Sheets is the only production database. Expense categories are Operational, Grocery, Drawings, and Other; owner drawings remain in histories and exports but are excluded from the estimated operating result. Existing legacy Daily Expenses default to Grocery. The application does not include inventory, PAYE, leave, loans, or paid services. Payroll supports optional overtime at 1.5× and public-holiday work at 2× the employee's hourly rate.

## Safety and data model

The app opens spreadsheet `1oX20BjwHKcvZECa5cDMOkN8iEOalF57AbznvGrynB0M` by key. It never deletes, clears, renames, or overwrites legacy worksheets. Initialization only creates missing application worksheets: `App_Settings`, `Sales_Data`, `Expenses_Data`, `Rent_Data`, `Employees`, `Payroll_Runs`, `Payroll_Details`, and `Audit_Log`.

Credentials are read only from Streamlit secrets and are never logged. The real `.streamlit/secrets.toml` is ignored by Git. Do not commit a JSON key or secrets file.

All business dates and timestamps use `Pacific/Apia`. Stored timestamps include their Samoa UTC offset, and the Google spreadsheet timezone should also be set to `Pacific/Apia`.

## Local setup

1. Install Python 3.11 or later.
2. Create and activate a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`.
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` locally.
5. Set `APP_USERNAME` and `APP_PASSWORD` to private values. Use a long, unique password and do not share it in source code or screenshots.
6. Fill in the service-account values locally. Preserve the private key; escaped `\n` values are supported.
7. Confirm the spreadsheet is shared as Editor with `codex-admin@waterfront-all-in-one.iam.gserviceaccount.com`.
8. Run `streamlit run app.py`.
9. Use **Initialise missing app sheets** once. This action does not modify legacy tabs.

For Streamlit Community Cloud, add the same TOML values—including `APP_USERNAME` and `APP_PASSWORD`—in the app's Secrets settings. Push source code to a private GitHub Free repository without `.streamlit/secrets.toml`.

## Payroll

Payroll uses `Decimal`, `ROUND_HALF_UP`, and two-decimal financial rounding. A run is not written until final confirmation. Finalization creates a `Processing` run, writes and verifies details, recalculates totals, changes the run to `Finalized`, and writes the audit event. A failure attempts to mark the run `Failed` and reports that partial detail writes may exist. Finalized runs can only be voided and recreated. Employee rates and names are snapshotted into payroll details.

PDF payslips, combined payslips, payroll summaries, Excel workbooks, CSV files, and ZIP archives are generated in memory. Nothing is uploaded to Google Drive.

## Migration

Migration is a separate CLI process and defaults to dry-run:

```powershell
python scripts/migrate_legacy_data.py
python scripts/migrate_legacy_data.py --dry-run
python scripts/migrate_legacy_data.py --apply
```

The first two commands inspect and produce `migration_report.json` without writes. `--apply` first backs up every worksheet as CSV under `backups/<timestamp>/` and creates a manifest; it aborts if backup fails. Source sheets are never overwritten. Deterministic IDs make repeated migration attempts skip imported sales, expense, and rent records.

Legacy payroll layouts are highly format-dependent. The parser detects repeated pay-period blocks and employee/gross tables, ignores totals and PDF links, and skips unrecognized blocks. The dry run reports detected counts; review every detected run, employee, rate, and amount before apply. Run `python scripts/inspect_sheet.py` to list worksheet dimensions without printing credentials.

## Testing

```powershell
python -m compileall app.py src scripts tests
python -m pytest -q
```

Tests cover payroll examples and rounding, validators, repository conversion, deterministic migration parsing, PDF creation, and CSV/Excel/ZIP generation. Repository tests do not contact Google Sheets.

## Structure

- `app.py` — Streamlit shell and navigation
- `src/config.py` — schema, settings, branding, timezone, currency
- `src/sheets_client.py` — secure connection and safe sheet initialization
- `src/repositories.py` — centralized data access
- `src/calculations.py`, `src/validators.py` — business rules
- `src/pdf_generator.py`, `src/exports.py` — in-memory documents
- `src/migration.py`, `scripts/` — migration and inspection tools
- `src/pages/` — the eight application pages
- `tests/` — offline unit tests

## Production checklist

- Add the real credentials only to Streamlit secrets.
- Run the migration dry-run and review `migration_report.json`.
- Inspect legacy headers and payroll blocks.
- Confirm the backup folder and manifest before `--apply`.
- Initialize missing app sheets.
- Verify two sample payroll calculations and PDFs before normal use.
- Keep the service account scoped to the target spreadsheet and rotate the key if exposed.
