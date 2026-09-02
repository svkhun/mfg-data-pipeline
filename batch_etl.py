import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text

# ตั้งค่า Logging บนหน้าจอ Console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

DB_URI = "postgresql+psycopg2://mfg_user:mfg_password@localhost:5432/manufacturing_db"

def run_batch_etl():
    pipeline_name = "hourly_oee_batch_aggregation"
    start_time = datetime.now()
    engine = create_engine(DB_URI)
    
    logging.info(f"Starting batch pipeline: {pipeline_name}")

    # SQL Query สำหรับ Extract, Transform, และ Upsert ลง Data Mart
    etl_query = text("""
    INSERT INTO hourly_production_summary (
        hour_bucket,
        line_id,
        machine_id,
        total_cycles,
        total_good_units,
        total_defect_units,
        total_produced_units,
        operating_time_sec,
        unplanned_downtime_sec,
        planned_downtime_sec,
        idle_time_sec,
        availability_pct,
        performance_pct,
        quality_pct,
        oee_pct
    )
    WITH raw_metrics AS (
        SELECT 
            DATE_TRUNC('hour', t.timestamp) AS hour_bucket,
            t.line_id,
            t.machine_id,
            COUNT(t.event_id) AS total_cycles,
            SUM(t.good_units) AS total_good_units,
            SUM(t.defect_units) AS total_defect_units,
            SUM(t.good_units + t.defect_units) AS total_produced_units,
            SUM(CASE WHEN t.status_code = 1 THEN t.cycle_time_sec ELSE 0 END) AS operating_time_sec,
            SUM(CASE WHEN r.category = 'Unplanned Downtime' THEN t.cycle_time_sec ELSE 0 END) AS unplanned_downtime_sec,
            SUM(CASE WHEN r.category = 'Planned Maintenance' THEN t.cycle_time_sec ELSE 0 END) AS planned_downtime_sec,
            SUM(CASE WHEN r.category = 'Idle' THEN t.cycle_time_sec ELSE 0 END) AS idle_time_sec,
            CASE 
                WHEN t.machine_id = 'CNC_A' THEN 12.0
                WHEN t.machine_id = 'CNC_B' THEN 15.0
                WHEN t.machine_id = 'ROBOT_ARM' THEN 8.0
                ELSE 10.0
            END AS ideal_cycle_time_sec
        FROM machine_telemetry t
        JOIN downtime_reasons r ON t.status_code = r.status_code
        GROUP BY DATE_TRUNC('hour', t.timestamp), t.line_id, t.machine_id
    ),
    calculated_oee AS (
        SELECT 
            hour_bucket,
            line_id,
            machine_id,
            total_cycles,
            total_good_units,
            total_defect_units,
            total_produced_units,
            operating_time_sec,
            unplanned_downtime_sec,
            planned_downtime_sec,
            idle_time_sec,
            ROUND(
                (operating_time_sec / NULLIF(operating_time_sec + unplanned_downtime_sec, 0)) * 100.0, 
                2
            ) AS availability_pct,
            ROUND(
                LEAST(((ideal_cycle_time_sec * total_produced_units) / NULLIF(operating_time_sec, 0)) * 100.0, 100.0), 
                2
            ) AS performance_pct,
            ROUND(
                (total_good_units::NUMERIC / NULLIF(total_produced_units, 0)) * 100.0, 
                2
            ) AS quality_pct
        FROM raw_metrics
    )
    SELECT 
        hour_bucket,
        line_id,
        machine_id,
        total_cycles,
        total_good_units,
        total_defect_units,
        total_produced_units,
        operating_time_sec,
        unplanned_downtime_sec,
        planned_downtime_sec,
        idle_time_sec,
        COALESCE(availability_pct, 0.00) AS availability_pct,
        COALESCE(performance_pct, 0.00) AS performance_pct,
        COALESCE(quality_pct, 0.00) AS quality_pct,
        ROUND(
            (COALESCE(availability_pct, 0.00) * COALESCE(performance_pct, 0.00) * COALESCE(quality_pct, 0.00)) / 10000.0, 
            2
        ) AS oee_pct
    FROM calculated_oee
    ON CONFLICT (hour_bucket, line_id, machine_id) 
    DO UPDATE SET
        total_cycles = EXCLUDED.total_cycles,
        total_good_units = EXCLUDED.total_good_units,
        total_defect_units = EXCLUDED.total_defect_units,
        total_produced_units = EXCLUDED.total_produced_units,
        operating_time_sec = EXCLUDED.operating_time_sec,
        unplanned_downtime_sec = EXCLUDED.unplanned_downtime_sec,
        planned_downtime_sec = EXCLUDED.planned_downtime_sec,
        idle_time_sec = EXCLUDED.idle_time_sec,
        availability_pct = EXCLUDED.availability_pct,
        performance_pct = EXCLUDED.performance_pct,
        quality_pct = EXCLUDED.quality_pct,
        oee_pct = EXCLUDED.oee_pct,
        created_at = CURRENT_TIMESTAMP;
    """)

    log_query = text("""
    INSERT INTO pipeline_execution_logs (pipeline_name, start_time, end_time, status, rows_processed, error_message)
    VALUES (:p_name, :s_time, :e_time, :status, :rows, :err);
    """)

    try:
        with engine.begin() as conn:
            result = conn.execute(etl_query)
            rows_affected = result.rowcount
            end_time = datetime.now()
            
            # บันทึกสถานะ SUCCESS ลง Logs
            conn.execute(log_query, {
                "p_name": pipeline_name,
                "s_time": start_time,
                "e_time": end_time,
                "status": "SUCCESS",
                "rows": rows_affected,
                "err": None
            })
            
        logging.info(f"Pipeline executed successfully. Processed/Upserted {rows_affected} records.")
        logging.info(f"Execution time: {(end_time - start_time).total_seconds():.2f} seconds.")

    except Exception as e:
        end_time = datetime.now()
        logging.error(f"Pipeline failed: {str(e)}")
        
        # บันทึกสถานะ FAILED ลง Logs
        try:
            with engine.begin() as conn:
                conn.execute(log_query, {
                    "p_name": pipeline_name,
                    "s_time": start_time,
                    "e_time": end_time,
                    "status": "FAILED",
                    "rows": 0,
                    "err": str(e)
                })
        except Exception as log_err:
            logging.error(f"Failed to write error log: {str(log_err)}")
        
        sys.exit(1)

if __name__ == "__main__":
    run_batch_etl()