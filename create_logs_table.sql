CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
    log_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(20) NOT NULL, -- 'SUCCESS' หรือ 'FAILED'
    rows_processed INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);