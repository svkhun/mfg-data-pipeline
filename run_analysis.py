import pandas as pd
from sqlalchemy import create_engine

# ตั้งค่าให้ Pandas แสดงคอลัมน์และตารางได้กว้างขึ้น
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

engine = create_engine("postgresql+psycopg2://mfg_user:mfg_password@localhost:5432/manufacturing_db")

print("\n" + "="*80)
print(" MANUFACTURING DATA MART: HOURLY OEE & PRODUCTION REPORT ")
print("="*80)

# Query ดึงข้อมูล OEE ครบ 3 เสาหลักจาก Data Mart Table
query = """
SELECT 
    TO_CHAR(hour_bucket, 'YYYY-MM-DD HH24:MI') AS hour,
    line_id,
    machine_id,
    total_produced_units AS produced,
    total_good_units AS good,
    total_defect_units AS defect,
    availability_pct AS avail_pct,
    performance_pct AS perf_pct,
    quality_pct AS qual_pct,
    oee_pct
FROM hourly_production_summary
ORDER BY hour_bucket DESC, line_id, machine_id;
"""

df_oee = pd.read_sql_query(query, engine)
print(df_oee.to_string(index=False))

print("\n" + "-"*80)
print(" LINE-LEVEL OEE BENCHMARK ")
print("-"*80)

# สรุป OEE เฉลี่ยรายสายการผลิต (Line ID)
query_line_summary = """
SELECT 
    line_id,
    SUM(total_produced_units) AS total_units,
    ROUND(AVG(availability_pct), 2) AS avg_availability,
    ROUND(AVG(performance_pct), 2) AS avg_performance,
    ROUND(AVG(quality_pct), 2) AS avg_quality,
    ROUND(AVG(oee_pct), 2) AS avg_oee
FROM hourly_production_summary
GROUP BY line_id
ORDER BY avg_oee DESC;
"""

df_line = pd.read_sql_query(query_line_summary, engine)
print(df_line.to_string(index=False))
print("="*80 + "\n")