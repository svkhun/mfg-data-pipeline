import time
import random
import psycopg2
from datetime import datetime

# เชื่อมต่อ Database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="manufacturing_db",
    user="mfg_user",
    password="mfg_password"
)
cursor = conn.cursor()

lines = ["LINE_01", "LINE_02"]
machines = ["CNC_A", "CNC_B", "ROBOT_ARM"]

print("Starting Line Data Ingestion Simulator (Ctrl+C to stop)...")

try:
    while True:
        line = random.choice(lines)
        machine = random.choice(machines)
        
        # จำลองสถานะ (ความน่าจะเป็น: ปกติ 80%, มีปัญหา 20%)
        status = random.choices([1, 2, 3, 4, 5], weights=[80, 5, 5, 5, 5])[0]
        
        if status == 1:
            cycle_time = round(random.uniform(8.5, 12.0), 2)
            good_units = random.randint(1, 3)
            defect_units = 1 if random.random() < 0.05 else 0
        else:
            cycle_time = round(random.uniform(15.0, 45.0), 2)
            good_units = 0
            defect_units = 0

        query = """
        INSERT INTO machine_telemetry (line_id, machine_id, timestamp, cycle_time_sec, good_units, defect_units, status_code)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(query, (line, machine, datetime.now(), cycle_time, good_units, defect_units, status))
        conn.commit()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ingested: {line} | {machine} | Status: {status} | Good: {good_units}")
        time.sleep(2)

except KeyboardInterrupt:
    print("\nSimulator stopped.")
finally:
    cursor.close()
    conn.close()