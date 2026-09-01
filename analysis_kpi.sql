SELECT 
    line_id,
    COUNT(event_id) AS total_cycles,
    SUM(good_units) AS total_good_units,
    SUM(defect_units) AS total_defect_units,
    ROUND((SUM(defect_units)::NUMERIC / NULLIF(SUM(good_units + defect_units), 0)) * 100, 2) AS defect_rate_pct
FROM machine_telemetry
GROUP BY line_id;

SELECT 
    t.line_id,
    t.machine_id,
    r.status_name,
    r.category,
    COUNT(*) AS incident_count,
    ROUND(SUM(t.cycle_time_sec), 2) AS total_lost_time_seconds
FROM machine_telemetry t
JOIN downtime_reasons r ON t.status_code = r.status_code
WHERE t.status_code != 1
GROUP BY t.line_id, t.machine_id, r.status_name, r.category
ORDER BY total_lost_time_seconds DESC

/* 
๋How to run this script:
    docker compose up -d 
    .\.venv\Scripts\python simulator.py
    Get-Content analysis_kpi.sql | docker exec -i mfg_postgres psql -U mfg_user -d manufacturing_db

็How to stop the containers:
    .\.venv\Scripts\python simulator.py --stop
    docker compose stop
    docker compose down
*/