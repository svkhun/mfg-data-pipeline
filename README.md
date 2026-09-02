# Real-Time & Batch Manufacturing Data Pipeline

An end-to-end data pipeline simulating IoT/PLC line telemetry from industrial machines, persisting raw streaming events into PostgreSQL via Docker, aggregating hourly OEE Data Marts, and orchestrating automated batch ETL pipelines with audit logging.

---

## 🏗️ Architecture Overview

```
+-------------------------------------------------------------------------------+
|                             Data Ingestion Layer                              |
|   simulator.py (Simulates IoT/PLC telemetry: cycle time, status, good/defect) |
+---------------------------------------+---------------------------------------+
                                        | (Stream Insert)
                                        v
+-------------------------------------------------------------------------------+
|                       PostgreSQL 15 (Docker Container)                        |
|                                                                               |
|   [Raw Telemetry Table]              [Master Table]                           |
|   machine_telemetry                  downtime_reasons                         |
+-------------------+-------------------+---------------------------------------+
                    |                                         |
     (Real-time Poll/Stream)             +--------------------+--------------------+
                    |                    |                                         |
                    v                    v (Extract & Transform)                   v (Extract & Transform)
+---------------------------------------+   +-----------------------------------+   +-----------------------------------+
|  Stateful Stream Monitor & Detector   |   |       Automated Batch ETL         |   |        SQL Data Mart Engine       |
|  stream_monitor.py                    |   |  batch_etl.py (Idempotent Upsert) |   |        populate_datamart.sql      |
|  - Data Quality Gate                  |   +-----------------+-----------------+   +-----------------+-----------------+
|  - Breakdown & Defect Streak Alerts   |                     |                                       |
+---------------------------------------+                     +-------------------+-------------------+
                                                                                  |
                                                                                  v (Load / Upsert)
+-------------------------------------------------------------------------------+
|                             Data Mart & Analytics                             |
|                                                                               |
|   [Aggregated Data Mart]             [Audit Logging]                          |
|   hourly_production_summary          pipeline_execution_logs                  |
|   (OEE = Availability x Performance x Quality)                                |
|                                                                               |
|   Analytics & Reporting: run_analysis.py                                      |
|   Orchestration & Scheduling: scheduler.py (1-minute intervals)               |
+-------------------------------------------------------------------------------+
```

* **Data Ingestion:** Event-driven telemetry stream simulator ([`simulator.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/simulator.py))
* **Real-Time Stateful Stream Monitor:** Event listener with data quality gates, critical breakdown alerts, and consecutive quality spike detection ([`stream_monitor.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/stream_monitor.py))
* **Storage Layer:** PostgreSQL 15 deployed on Docker with volume persistence ([`docker-compose.yml`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/docker-compose.yml))
* **Data Mart:** Aggregated hourly table calculating Availability, Performance, Quality, and OEE ([`create_datamart.sql`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/create_datamart.sql))
* **Automated Batch ETL:** Python-based idempotent Upsert pipeline with execution auditing ([`batch_etl.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/batch_etl.py))
* **Orchestration:** Periodic scheduler running automated batch cycles ([`scheduler.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/scheduler.py))
* **Audit Logging:** Execution metadata, row counts, and status tracking ([`create_logs_table.sql`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/create_logs_table.sql))
* **Analytics Engine:** Multi-level terminal KPI report ([`run_analysis.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/run_analysis.py))

---

## 📈 OEE Mathematical Model

Overall Equipment Effectiveness (OEE) is calculated across three core pillars:

$$\text{OEE} = \text{Availability} \times \text{Performance} \times \text{Quality}$$

| Pillar | Formula | Description |
| :--- | :--- | :--- |
| **Availability ($A$)** | $\frac{\text{Operating Time}}{\text{Operating Time} + \text{Unplanned Downtime}} \times 100$ | Percentage of planned production time the machine was actively running. |
| **Performance ($P$)** | $\min\left(\frac{\text{Ideal Cycle Time} \times \text{Total Produced Units}}{\text{Operating Time}} \times 100,\, 100\right)$ | Operating speed efficiency relative to designed ideal cycle times. |
| **Quality ($Q$)** | $\frac{\text{Total Good Units}}{\text{Total Produced Units}} \times 100$ | Ratio of defect-free products produced against total units. |
| **Overall OEE** | $\frac{A \times P \times Q}{10000}$ | Holistic measure of manufacturing operational efficiency. |

### Machine Ideal Cycle Times
* **CNC_A:** 12.0 seconds/unit
* **CNC_B:** 15.0 seconds/unit
* **ROBOT_ARM:** 8.0 seconds/unit
* **Default:** 10.0 seconds/unit

---

## 🗓️ Weekly Milestones & Core Capabilities

### Week 1: Data Mart & Full OEE Modeling
- Established [`hourly_production_summary`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/create_datamart.sql) Data Mart table with unique constraint on `(hour_bucket, line_id, machine_id)`.
- Implemented comprehensive SQL CTE aggregations in [`populate_datamart.sql`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/populate_datamart.sql) computing Availability, Performance, Quality, and Overall OEE with `ON CONFLICT DO UPDATE` upsert logic.
- Built [`run_analysis.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/run_analysis.py) for terminal OEE visualization and line-level benchmarking.

### Week 2: Automated Batch ETL & Orchestration
- Developed [`batch_etl.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/batch_etl.py) using SQLAlchemy to extract raw telemetry, calculate OEE metrics, and perform idempotent upserts into the Data Mart.
- Created [`pipeline_execution_logs`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/create_logs_table.sql) table to maintain execution audits, tracking start/end times, durations, processed row counts, status (`SUCCESS` / `FAILED`), and error tracebacks.
- Deployed periodic execution loop via [`scheduler.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/scheduler.py) using the Python `schedule` library to automate recurring batch cycles.

### Week 3: Stateful Real-Time Stream Monitoring & Anomaly Detection
- Built [`stream_monitor.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/stream_monitor.py) for real-time stateful stream analytics and edge anomaly detection:
  - **Data Quality Gate:** Rejects corrupted telemetry (e.g. invalid or non-positive cycle times).
  - **Critical Breakdown Alerts:** Real-time flagging of Unplanned Downtime incidents with color-coded ANSI logging.
  - **Stateful In-Memory Quality Spike Alerts:** Uses in-memory state tracking (`defaultdict`) per machine (`line_id + machine_id`) to detect consecutive defect spikes ($\ge 2$ consecutive defect events) and automatically resets upon recovering normal production.

---

## 💻 Complete Command Guide

### 1. Project Setup & Dependencies
```powershell
# Create Virtual Environment
python -m venv .venv

# Activate Virtual Environment (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install Required Libraries
.\.venv\Scripts\pip install psycopg2-binary pandas sqlalchemy schedule
```

---

### 2. Infrastructure Deployment (PostgreSQL via Docker)
```powershell
# Start PostgreSQL container in background
docker compose up -d

# Verify container is running and healthy
docker ps --filter "name=mfg_postgres"
```

---

### 3. Database Schema Setup
Initialize master tables, telemetry storage, Data Mart table, and audit log table:
```powershell
# Initialize Base Schema & Master Data (executed automatically on first compose up, or run manually):
Get-Content init_db.sql | docker exec -i mfg_postgres psql -U mfg_user -d manufacturing_db

# Create Data Mart Table & Indexes
Get-Content create_datamart.sql | docker exec -i mfg_postgres psql -U mfg_user -d manufacturing_db

# Create Pipeline Execution Logs Table
Get-Content create_logs_table.sql | docker exec -i mfg_postgres psql -U mfg_user -d manufacturing_db
```

---

### 4. Running the Pipeline Components

#### Terminal 1: Ingestion Simulator
Start continuous telemetry streaming (generates events every 2 seconds):
```powershell
.\.venv\Scripts\python simulator.py
```
*(Press `Ctrl+C` to stop)*

#### Terminal 2: Real-Time Stateful Stream Monitor & Anomaly Detector
Monitor incoming events in real time with state tracking, quality gates, and streak alerts:
```powershell
.\.venv\Scripts\python stream_monitor.py
```
*(Press `Ctrl+C` to stop)*

#### Terminal 3: Automated Batch ETL Scheduler
Automate recurring 1-minute aggregation cycles with audit logging:
```powershell
.\.venv\Scripts\python scheduler.py
```

#### Terminal 4 (Ad-hoc): Manual Batch ETL & KPI Reports
```powershell
# Manually trigger one-time Batch ETL upsert
.\.venv\Scripts\python batch_etl.py

# Print multi-level OEE & Line benchmark report
.\.venv\Scripts\python run_analysis.py
```

---

### 5. Direct Database Inspection & Auditing

Connect to PostgreSQL CLI inside Docker:
```powershell
docker exec -it mfg_postgres psql -U mfg_user -d manufacturing_db
```

#### Useful SQL Audit Queries:

```sql
-- Check Data Mart OEE Summary records
SELECT hour_bucket, line_id, machine_id, total_produced_units, availability_pct, performance_pct, quality_pct, oee_pct 
FROM hourly_production_summary 
ORDER BY hour_bucket DESC, line_id, machine_id;

-- Inspect Batch Pipeline Execution Audit Logs
SELECT log_id, pipeline_name, start_time, end_time, status, rows_processed, error_message 
FROM pipeline_execution_logs 
ORDER BY log_id DESC 
LIMIT 10;

-- Check Raw Telemetry Volume
SELECT line_id, machine_id, COUNT(*) AS event_count, SUM(good_units) AS total_good, SUM(defect_units) AS total_defect 
FROM machine_telemetry 
GROUP BY line_id, machine_id;
```

---

### 6. Teardown & Maintenance
```powershell
# Stop PostgreSQL container (data is preserved in docker volume)
docker compose stop

# Destroy container and networks
docker compose down

# Destroy container and wipe data volumes (Clean reset)
docker compose down -v
```

---

## 🗄️ Database Schema Reference

### `machine_telemetry` (Raw Stream Events)
| Column | Type | Description |
| :--- | :--- | :--- |
| `event_id` | `BIGSERIAL PRIMARY KEY` | Auto-incrementing unique event identifier |
| `line_id` | `VARCHAR(20)` | Production line identifier (`LINE_01`, `LINE_02`) |
| `machine_id` | `VARCHAR(20)` | Industrial machine identifier (`CNC_A`, `CNC_B`, `ROBOT_ARM`) |
| `timestamp` | `TIMESTAMPTZ` | Timestamp when event occurred |
| `cycle_time_sec` | `NUMERIC(6,2)` | Machine cycle duration in seconds |
| `good_units` | `INT` | Count of quality-approved units |
| `defect_units` | `INT` | Count of rejected / defect units |
| `status_code` | `INT REFERENCES downtime_reasons` | Current machine status code |

### `hourly_production_summary` (Aggregated Data Mart)
| Column | Type | Description |
| :--- | :--- | :--- |
| `summary_id` | `SERIAL PRIMARY KEY` | Unique record ID |
| `hour_bucket` | `TIMESTAMP` | Truncated hourly time window |
| `line_id` | `VARCHAR(50)` | Production line identifier |
| `machine_id` | `VARCHAR(50)` | Machine identifier |
| `total_cycles` | `INT` | Total event count in the hour |
| `total_good_units` | `INT` | Total defect-free units produced |
| `total_defect_units` | `INT` | Total defective units produced |
| `total_produced_units` | `INT` | Total production output (`good + defect`) |
| `operating_time_sec` | `NUMERIC(10,2)` | Time spent in normal production (`status_code = 1`) |
| `unplanned_downtime_sec` | `NUMERIC(10,2)` | Time lost to unplanned breakdowns |
| `planned_downtime_sec` | `NUMERIC(10,2)` | Time allocated for maintenance / tool change |
| `idle_time_sec` | `NUMERIC(10,2)` | Time spent idle (no material) |
| `availability_pct` | `NUMERIC(5,2)` | Machine availability percentage |
| `performance_pct` | `NUMERIC(5,2)` | Machine speed efficiency percentage |
| `quality_pct` | `NUMERIC(5,2)` | Production yield quality percentage |
| `oee_pct` | `NUMERIC(5,2)` | Overall Equipment Effectiveness percentage |
| `created_at` | `TIMESTAMP` | Timestamp of last upsert |

### `pipeline_execution_logs` (ETL Audit Log)
| Column | Type | Description |
| :--- | :--- | :--- |
| `log_id` | `SERIAL PRIMARY KEY` | Auto-incrementing audit log identifier |
| `pipeline_name` | `VARCHAR(100)` | Name of the executing ETL pipeline |
| `start_time` | `TIMESTAMP` | Batch execution start timestamp |
| `end_time` | `TIMESTAMP` | Batch execution end timestamp |
| `status` | `VARCHAR(20)` | Run status (`SUCCESS` or `FAILED`) |
| `rows_processed` | `INT` | Number of rows affected / upserted |
| `error_message` | `TEXT` | Traceback or error details if failed |
| `created_at` | `TIMESTAMP` | Log record timestamp |