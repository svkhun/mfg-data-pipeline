import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://mfg_user:mfg_password@localhost:5432/manufacturing_db")

with open("analysis_kpi.sql", "r", encoding="utf-8") as f:
    raw_queries = f.read().split(";")

query_idx = 1
for raw_query in raw_queries:
    query = raw_query.strip()
    if query:  # ตรวจสอบว่าไม่ใช่ข้อความว่าง
        print(f"\n==================== KPI Query {query_idx} Result ====================")
        df = pd.read_sql_query(query, engine)
        print(df.to_string(index=False))
        query_idx += 1

print("\nAnalysis completed successfully.")