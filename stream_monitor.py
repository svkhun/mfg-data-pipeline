import sys
import time
import logging
from collections import defaultdict
from sqlalchemy import create_engine, text

# ตั้งค่า Logging Format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

DB_URI = "postgresql+psycopg2://mfg_user:mfg_password@localhost:5432/manufacturing_db"
engine = create_engine(DB_URI)

# ตัวแปรจำสถานะของเสียสะสมต่อเนื่อง: key = "LINE_ID_MACHINE_ID", value = จำนวนครั้งที่ติดกัน
consecutive_defects = defaultdict(int)

def monitor_stream():
    logging.info("Starting Stateful Real-Time Stream Monitoring & Anomaly Detector...")
    logging.info("Listening for streaming events with state tracking... (Press Ctrl+C to stop)")
    
    last_processed_id = 0

    # ดึง event_id ล่าสุดเป็นจุดเริ่มต้น เพื่อประมวลผลเฉพาะข้อมูลที่เข้ามาใหม่สดๆ
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT COALESCE(MAX(event_id), 0) FROM machine_telemetry;")).scalar()
            last_processed_id = res or 0
    except Exception as e:
        logging.error(f"Failed to fetch initial event id: {e}")

    while True:
        try:
            query = text("""
                SELECT 
                    t.event_id,
                    t.timestamp,
                    t.line_id,
                    t.machine_id,
                    t.status_code,
                    r.category,
                    r.status_name,
                    t.good_units,
                    t.defect_units,
                    t.cycle_time_sec
                FROM machine_telemetry t
                JOIN downtime_reasons r ON t.status_code = r.status_code
                WHERE t.event_id > :last_id
                ORDER BY t.event_id ASC
                LIMIT 50;
            """)

            with engine.connect() as conn:
                result = conn.execute(query, {"last_id": last_processed_id}).mappings().all()

            for row in result:
                last_processed_id = max(last_processed_id, row["event_id"])

                cycle = row["cycle_time_sec"]
                line = row["line_id"]
                machine = row["machine_id"]
                cat = row["category"]
                status_desc = row["status_name"]
                status = row["status_code"]
                defect = row["defect_units"]
                good = row["good_units"]
                machine_key = f"{line}_{machine}"

                # ----------------------------------------------------
                # 1. Data Quality Gate: กรองและเตือนข้อมูลผิดปกติทางกายภาพ
                # ----------------------------------------------------
                if cycle is None or cycle <= 0:
                    logging.error(f"[DATA QUALITY ERROR] Invalid cycle time ({cycle}s) at Event ID: {row['event_id']}")
                    continue

                # ----------------------------------------------------
                # 2. Critical Breakdown Alert: ตรวจจับ Unplanned Downtime
                # ----------------------------------------------------
                if cat == "Unplanned Downtime":
                    logging.warning(
                        f"\033[91m[CRITICAL BREAKDOWN ALERT] {line} | {machine} -> {status_desc} (Status: {status}) | Loss Time: {cycle:.2f}s\033[0m"
                    )

                # ----------------------------------------------------
                # 3. Consecutive Defect Spike Alert: ตรวจจับของเสียสะสมต่อเนื่อง
                # ----------------------------------------------------
                elif defect > 0:
                    consecutive_defects[machine_key] += 1
                    streak = consecutive_defects[machine_key]

                    if streak >= 2:
                        logging.error(
                            f"\033[95m[QUALITY SPIKE ALERT] {line} | {machine} -> {streak} CONSECUTIVE DEFECT EVENTS! (Latest: {defect} defect units)\033[0m"
                        )
                    else:
                        logging.warning(
                            f"\033[93m[DEFECT DETECTED] {line} | {machine} -> Defect Units: {defect} | Good Units: {good}\033[0m"
                        )

                # ----------------------------------------------------
                # 4. Healthy / Normal: ผลิตงานสมบูรณ์
                # ----------------------------------------------------
                else:
                    # รีเซ็ตตัวนับเมื่อเครื่องจักรผลิตงานดีกลับมาได้
                    consecutive_defects[machine_key] = 0
                    if cat != "Unplanned Downtime":
                        logging.info(f"[HEALTHY] {line} | {machine} -> Output: {good} units ({cycle:.2f}s)")

            time.sleep(2)

        except Exception as e:
            logging.error(f"Stream Monitor loop error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    try:
        monitor_stream()
    except KeyboardInterrupt:
        logging.info("Stream Monitor stopped cleanly by user.")
        sys.exit(0)