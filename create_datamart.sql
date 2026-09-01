-- สร้างตาราง Data Mart สำหรับเก็บข้อมูลสรุปรายชั่วโมง
CREATE TABLE IF NOT EXISTS hourly_production_summary (
    summary_id SERIAL PRIMARY KEY,
    hour_bucket TIMESTAMP NOT NULL,
    line_id VARCHAR(50) NOT NULL,
    machine_id VARCHAR(50) NOT NULL,
    total_cycles INT NOT NULL,
    total_good_units INT NOT NULL,
    total_defect_units INT NOT NULL,
    total_produced_units INT NOT NULL,
    operating_time_sec NUMERIC(10, 2) NOT NULL,
    unplanned_downtime_sec NUMERIC(10, 2) NOT NULL,
    planned_downtime_sec NUMERIC(10, 2) NOT NULL,
    idle_time_sec NUMERIC(10, 2) NOT NULL,
    availability_pct NUMERIC(5, 2) NOT NULL,
    performance_pct NUMERIC(5, 2) NOT NULL,
    quality_pct NUMERIC(5, 2) NOT NULL,
    oee_pct NUMERIC(5, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_hour_line_machine UNIQUE (hour_bucket, line_id, machine_id)
);

-- สร้าง Index เพื่อเพิ่มความเร็วในการ Query สรุปผลตามช่วงเวลา
CREATE INDEX IF NOT EXISTS idx_datamart_hour ON hourly_production_summary(hour_bucket);
CREATE INDEX IF NOT EXISTS idx_datamart_line_machine ON hourly_production_summary(line_id, machine_id); 