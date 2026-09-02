import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Industrial Real-Time & OEE Monitor", layout="wide")

# Auto Refresh หน้าจออัตโนมัติทุกๆ 3 วินาที
count = st_autorefresh(interval=3000, limit=None, key="live_refresh_counter")

DEFAULT_URI = "postgresql+psycopg2://mfg_user:mfg_password@localhost:5432/manufacturing_db"
DB_URI = os.getenv("DB_URI", DEFAULT_URI)
engine = create_engine(DB_URI)

st.title("🏭 Real-Time Line Telemetry & OEE Monitor")
st.caption(f"⚡ Live Polling Active (Cycle #{count}) — Updating every 3s")

# ----------------------------------------------------
# 1. Data Retrieval (Single Connection Scope)
# ----------------------------------------------------
try:
    with engine.connect() as conn:
        # ดึงสถานะล่าสุดของเครื่องจักรทุกตัว (ไม่ซ้ำ ไม่ล้นแถว)
        latest_machines_df = pd.read_sql("""
            SELECT DISTINCT ON (t.line_id, t.machine_id)
                t.event_id,
                t.timestamp,
                t.line_id,
                t.machine_id,
                r.status_name,
                r.category,
                t.good_units,
                t.defect_units,
                t.cycle_time_sec
            FROM machine_telemetry t
            JOIN downtime_reasons r ON t.status_code = r.status_code
            ORDER BY t.line_id, t.machine_id, t.event_id DESC;
        """, conn)

        # ดึง 10 Events ล่าสุดสำหรับ Live Table Feed
        live_df = pd.read_sql("""
            SELECT 
                t.event_id,
                t.timestamp,
                t.line_id,
                t.machine_id,
                r.status_name,
                r.category,
                t.good_units,
                t.defect_units,
                t.cycle_time_sec
            FROM machine_telemetry t
            JOIN downtime_reasons r ON t.status_code = r.status_code
            ORDER BY t.event_id DESC
            LIMIT 10;
        """, conn)

        # ดึง Historical OEE จาก Data Mart
        oee_df = pd.read_sql("""
            SELECT 
                hour_bucket,
                line_id,
                machine_id,
                availability_pct,
                performance_pct,
                quality_pct,
                oee_pct,
                total_good_units,
                total_defect_units,
                unplanned_downtime_sec
            FROM hourly_production_summary
            ORDER BY hour_bucket DESC;
        """, conn)

except Exception as e:
    st.error(f"Database Connection Error: {e}")
    st.stop()

# ----------------------------------------------------
# 2. Live Machine Status Cards (ล็อกแถว 4 ช่องคงที่)
# ----------------------------------------------------
st.subheader("🔴 Live Machine Health")

if not latest_machines_df.empty:
    cols = st.columns(len(latest_machines_df))

    for idx, (_, row) in enumerate(latest_machines_df.iterrows()):
        with cols[idx]:
            is_breakdown = row["category"] == "Unplanned Downtime"
            is_defect = row["defect_units"] > 0
            
            status_color = "red" if is_breakdown else ("orange" if is_defect else "green")
            
            st.metric(
                label=f"{row['line_id']} | {row['machine_id']}",
                value=f"{row['status_name']}",
                delta=f"-{row['defect_units']} Defect" if is_defect else f"+{row['good_units']} Good"
            )
            st.caption(f"Cycle: {row['cycle_time_sec']:.1f}s | :{status_color}[{row['category']}]")

st.divider()

# ----------------------------------------------------
# 3. Stream Feed & Historic OEE Charts
# ----------------------------------------------------
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("📡 Recent Telemetry Ingestion (Latest 10 Events)")
    st.dataframe(
        live_df[["event_id", "timestamp", "line_id", "machine_id", "status_name", "good_units", "defect_units", "cycle_time_sec"]],
        hide_index=True,
        width="stretch"
    )

with c2:
    st.subheader("📈 Hourly OEE Trend (Batch Layer)")
    if not oee_df.empty:
        fig_oee = px.line(
            oee_df, 
            x="hour_bucket", 
            y="oee_pct", 
            color="machine_id",
            markers=True,
            labels={"hour_bucket": "Time Bucket", "oee_pct": "OEE (%)"}
        )
        st.plotly_chart(fig_oee, width="stretch")
    else:
        st.info("No aggregated OEE data yet. Run `batch_etl.py` to populate.")