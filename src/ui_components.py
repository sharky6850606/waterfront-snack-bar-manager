import streamlit as st
import pandas as pd
from .config import money,samoa_datetime
from .exports import csv_bytes,excel_bytes

def inject_css():
    st.markdown("""<style>
    :root{--wf-red:#E52B2F;--wf-orange:#F58220;--wf-yellow:#FFC247;--wf-ink:#171717;--wf-muted:#6B6863;--wf-bg:#F6F3EE;--wf-card:#FFFFFF;--wf-line:#E8E1D8}
    .stApp{background:linear-gradient(145deg,#F8F5F0 0%,#F3EEE7 100%);color:var(--wf-ink)}
    [data-testid="stHeader"]{background:transparent;height:2.5rem}
    [data-testid="stSidebar"]{background:rgba(255,255,255,.96);border-right:1px solid var(--wf-line)}
    [data-testid="stSidebar"] [data-testid="stImage"] img{border-radius:22px;box-shadow:0 12px 30px rgba(11,11,11,.14)}
    [data-testid="stSidebar"] h1{font-size:1.45rem;line-height:1.15;letter-spacing:-.03em;margin-top:.65rem}
    [data-testid="stSidebar"] [role="radiogroup"] label{border-radius:12px;padding:.42rem .65rem;margin:.08rem 0;transition:all .15s ease}
    [data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#F9EDEA;transform:translateX(2px)}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:linear-gradient(90deg,#FCE8E6,#FFF4E8);font-weight:700;color:#B7191E}
    .block-container{max-width:1380px;padding-top:2rem;padding-bottom:4rem}
    .wf-hero{position:relative;overflow:hidden;background:linear-gradient(120deg,#0B0B0B 0%,#24201D 62%,#5A1D16 100%);padding:1.65rem 1.8rem;border-radius:22px;margin:.2rem 0 1.45rem;box-shadow:0 18px 42px rgba(35,25,20,.13)}
    .wf-hero:after{content:"";position:absolute;width:230px;height:230px;border-radius:50%;right:-60px;top:-110px;background:radial-gradient(circle,#FFC24755 0%,#F5822011 65%,transparent 66%)}
    .wf-eyebrow{color:#FFC247;font-size:.72rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase;margin-bottom:.35rem}
    .wf-hero h1{color:white!important;font-size:clamp(1.75rem,3vw,2.6rem);letter-spacing:-.045em;margin:0 0 .3rem!important}
    .wf-hero p{color:#E7DED5;margin:0;max-width:780px;font-size:.98rem}
    .wf-pnl{background:linear-gradient(135deg,#FFFFFF 0%,#FFF9F3 100%);border:1px solid var(--wf-line);border-radius:20px;padding:1.35rem 1.45rem;margin:.55rem 0 1.45rem;box-shadow:0 10px 28px rgba(39,31,24,.065)}
    .wf-pnl-title{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;margin-bottom:1rem}.wf-pnl-title h3{margin:0!important;font-size:1.28rem}.wf-pnl-title span{color:var(--wf-muted);font-size:.82rem}
    .wf-pnl-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:1.35rem}.wf-pnl-row{display:flex;justify-content:space-between;gap:1rem;padding:.48rem 0;border-bottom:1px solid #EEE6DC}.wf-pnl-row:last-child{border-bottom:0}.wf-pnl-row strong{font-variant-numeric:tabular-nums}.wf-pnl-result{background:#F2F8F0;border:1px solid #D7E9D1;border-radius:15px;padding:1rem 1.1rem;display:flex;flex-direction:column;justify-content:center}.wf-pnl-result.negative{background:#FFF0EF;border-color:#F2CECB}.wf-pnl-result small{color:var(--wf-muted);font-weight:700;text-transform:uppercase;letter-spacing:.08em}.wf-pnl-result b{font-size:clamp(1.7rem,3vw,2.45rem);letter-spacing:-.045em;margin:.25rem 0}.wf-pnl-result em{font-style:normal;color:var(--wf-muted)}
    h2,h3{letter-spacing:-.035em;color:var(--wf-ink)}
    [data-testid="stMetric"]{background:rgba(255,255,255,.96);padding:1.2rem 1.25rem;border:1px solid var(--wf-line);border-radius:17px;box-shadow:0 7px 20px rgba(39,31,24,.055);min-height:142px;overflow:visible;transition:transform .15s ease,box-shadow .15s ease}
    [data-testid="stMetric"]:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(39,31,24,.09)}
    [data-testid="stMetricValue"],[data-testid="stMetricValue"]>div{font-size:clamp(1.4rem,2.2vw,2.15rem);white-space:normal!important;overflow:visible!important;text-overflow:clip!important;letter-spacing:-.045em;line-height:1.12}
    [data-testid="stMetricLabel"],[data-testid="stMetricLabel"]>div{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;color:var(--wf-muted);font-weight:650;line-height:1.25}
    [data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--wf-line)!important;border-radius:18px!important;background:rgba(255,255,255,.72);box-shadow:0 7px 22px rgba(39,31,24,.045)}
    .stButton>button,.stDownloadButton>button{border-radius:12px;min-height:44px;font-weight:700;border:1px solid #DCD3C9;transition:all .15s ease}
    .stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--wf-red);color:var(--wf-red);transform:translateY(-1px);box-shadow:0 7px 18px rgba(229,43,47,.12)}
    .stButton>button[kind="primary"]{background:linear-gradient(135deg,var(--wf-red),#BE171D);border:0;color:white}
    [data-baseweb="input"]>div,[data-baseweb="select"]>div,textarea{border-radius:12px!important;border-color:#DED6CC!important;background:#FFFEFC!important}
    [data-baseweb="tab-list"]{gap:.35rem;border-bottom:1px solid var(--wf-line)}
    [data-baseweb="tab"]{border-radius:11px 11px 0 0;padding:.7rem 1rem;font-weight:700}
    [data-testid="stDataFrame"]{border:1px solid var(--wf-line);border-radius:15px;overflow:hidden;background:white}
    [data-testid="stAlert"]{border-radius:14px}
    hr{border-color:var(--wf-line)}
    @media(max-width:760px){.block-container{padding:.9rem .8rem 3rem}.wf-hero{padding:1.25rem;border-radius:17px}.wf-hero p{font-size:.9rem}.wf-pnl-grid{grid-template-columns:1fr}.wf-pnl{padding:1rem}[data-testid="stMetric"]{min-height:108px;padding:.85rem}[data-testid="stMetricValue"]{font-size:1.5rem}[data-testid="column"]{min-width:100%!important}}
    </style>""",unsafe_allow_html=True)

def page_header(title,subtitle,eyebrow="Waterfront Snack Bar"):
    st.markdown(f'<section class="wf-hero"><div class="wf-eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></section>',unsafe_allow_html=True)

def pnl_summary_card(sales,expense_totals,rent,gross_payroll,result,money_formatter):
    operating_expenses=float(expense_totals["Operating_Total"]); costs=operating_expenses+float(rent)+float(gross_payroll); margin=(float(result)/float(sales)*100) if float(sales) else 0; state="" if float(result)>=0 else " negative"; label="Estimated operating surplus" if float(result)>=0 else "Estimated operating deficit"
    st.markdown(f'''<section class="wf-pnl"><div class="wf-pnl-title"><div><h3>P&amp;L Summary — Start to Today</h3><span>Internal management view · Samoa time</span></div><span>Automatically updated</span></div><div class="wf-pnl-grid"><div><div class="wf-pnl-row"><span>Sales revenue</span><strong>{money_formatter(sales)}</strong></div><div class="wf-pnl-row"><span>Operational expenses</span><strong>− {money_formatter(expense_totals["Operational"])}</strong></div><div class="wf-pnl-row"><span>Grocery expenses</span><strong>− {money_formatter(expense_totals["Grocery"])}</strong></div><div class="wf-pnl-row"><span>Other expenses</span><strong>− {money_formatter(expense_totals["Other"])}</strong></div><div class="wf-pnl-row"><span>Rent</span><strong>− {money_formatter(rent)}</strong></div><div class="wf-pnl-row"><span>Gross payroll</span><strong>− {money_formatter(gross_payroll)}</strong></div><div class="wf-pnl-row"><span><b>Total operating costs</b></span><strong>{money_formatter(costs)}</strong></div><div class="wf-pnl-row"><span>Owner drawings (excluded from P&amp;L)</span><strong>{money_formatter(expense_totals["Drawings"])}</strong></div></div><div class="wf-pnl-result{state}"><small>{label}</small><b>{money_formatter(result)}</b><em>Estimated margin: {margin:,.1f}%</em></div></div></section>''',unsafe_allow_html=True)
def history_table(records, key):
    if not records: st.info("No records yet."); return
    display=[]
    for record in records:
        row=dict(record)
        for field in ("Created_At","Updated_At","Timestamp"):
            if field in row: row[field]=samoa_datetime(row[field])
        display.append(row)
    st.dataframe(pd.DataFrame(display),width="stretch",hide_index=True)
    a,b=st.columns(2); a.download_button("Download CSV",csv_bytes(records),f"{key}.csv","text/csv",key=f"{key}_csv"); b.download_button("Download Excel",excel_bytes({key:records}),f"{key}.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",key=f"{key}_xlsx")
def guarded_load(repo):
    try: return repo.all()
    except Exception as exc: st.error(str(exc)); return []
