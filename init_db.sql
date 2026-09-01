-- Master Table: Machine Status
CREATE TABLE IF NOT EXISTS downtime_reasons (
    status_code INT PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL,
    category VARCHAR(30) NOT NULL
);

INSERT INTO downtime_reasons (status_code, status_name, category) VALUES
(1, 'Running Normal', 'Production'),
(2, 'Tool Change', 'Planned Maintenance'),
(3, 'Mechanical Jam', 'Unplanned Downtime'),
(4, 'Sensor Fault', 'Unplanned Downtime'),
(5, 'No Material', 'Idle')
ON CONFLICT (status_code) DO NOTHING;

-- Telemetry Table: Live Line Events
CREATE TABLE IF NOT EXISTS machine_telemetry (
    event_id BIGSERIAL PRIMARY KEY,
    line_id VARCHAR(20) NOT NULL,
    machine_id VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cycle_time_sec NUMERIC(6, 2) NOT NULL,
    good_units INT DEFAULT 0,
    defect_units INT DEFAULT 0,
    status_code INT REFERENCES downtime_reasons(status_code)
);

CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON machine_telemetry (timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_line ON machine_telemetry (line_id, machine_id);