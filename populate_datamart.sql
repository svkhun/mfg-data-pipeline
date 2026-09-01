-- คำนวณ Metric รายชั่วโมง และ Upsert ข้อมูลลง Data Mart Table
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
        
        -- รวมเวลาตามประเภทสถานะ
        SUM(CASE WHEN t.status_code = 1 THEN t.cycle_time_sec ELSE 0 END) AS operating_time_sec,
        SUM(CASE WHEN r.category = 'Unplanned Downtime' THEN t.cycle_time_sec ELSE 0 END) AS unplanned_downtime_sec,
        SUM(CASE WHEN r.category = 'Planned Maintenance' THEN t.cycle_time_sec ELSE 0 END) AS planned_downtime_sec,
        SUM(CASE WHEN r.category = 'Idle' THEN t.cycle_time_sec ELSE 0 END) AS idle_time_sec,
        
        -- กำหนด Ideal Cycle Time ต่อชิ้นตามประเภทเครื่องจักร
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

        -- 1. Availability (A) = Operating Time / (Operating Time + Unplanned Downtime)
        ROUND(
            (operating_time_sec / NULLIF(operating_time_sec + unplanned_downtime_sec, 0)) * 100.0, 
            2
        ) AS availability_pct,

        -- 2. Performance (P) = (Ideal Cycle Time * Total Produced) / Operating Time
        ROUND(
            LEAST(((ideal_cycle_time_sec * total_produced_units) / NULLIF(operating_time_sec, 0)) * 100.0, 100.0), 
            2
        ) AS performance_pct,

        -- 3. Quality (Q) = Good Units / Total Produced Units
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
    
    -- Overall OEE = (A * P * Q) / 10000
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