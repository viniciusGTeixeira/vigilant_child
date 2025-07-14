-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- Create tables for the pattern analyzer
CREATE TABLE IF NOT EXISTS detections (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    employee_id VARCHAR(50),
    location VARCHAR(100) NOT NULL,
    confidence FLOAT,
    attributes JSONB,
    face_info JSONB,
    badge_info JSONB
);

CREATE TABLE IF NOT EXISTS patterns (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confidence FLOAT
);

CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    employee_id VARCHAR(50),
    anomaly_type VARCHAR(50) NOT NULL,
    description TEXT,
    severity VARCHAR(20),
    pattern_data JSONB
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp);
CREATE INDEX IF NOT EXISTS idx_detections_employee ON detections(employee_id);
CREATE INDEX IF NOT EXISTS idx_patterns_employee ON patterns(employee_id);

-- Create hypertable for time-series data
SELECT create_hypertable('detections', 'timestamp', if_not_exists => TRUE);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin; 