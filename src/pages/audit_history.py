import streamlit as st
import pandas as pd
from ..repositories import AuditRepository
from ..ui_components import guarded_load,page_header

def render():
 page_header("Activity History","Review creates, updates, deletions, exports, finalizations, and voids."); rows=guarded_load(AuditRepository()); modules=sorted({str(r["Module"]) for r in rows}); actions=sorted({str(r["Action"]) for r in rows}); c1,c2=st.columns(2); module=c1.selectbox("Module",["All"]+modules); action=c2.selectbox("Action",["All"]+actions); record=st.text_input("Record ID"); search=st.text_input("Search text").lower(); dates=st.date_input("Date range",value=[])
 out=[r for r in rows if (module=="All" or r["Module"]==module) and (action=="All" or r["Action"]==action) and (not record or record in str(r["Record_ID"])) and (not search or search in str(r).lower())]
 if len(dates)==2: out=[r for r in out if dates[0].isoformat()<=str(r["Timestamp"])[:10]<=dates[1].isoformat()]
 st.dataframe(pd.DataFrame(out),width="stretch",hide_index=True) if out else st.info("No matching activity.")
