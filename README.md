# End-to-End Industrial IoT & OEE Manufacturing Data Platform

An enterprise-grade, Lambda/Hybrid manufacturing data platform designed for real-time edge telemetry ingestion, automated batch OEE (Overall Equipment Effectiveness) Data Mart aggregation, stateful stream anomaly detection, and containerized operational BI dashboarding.

---

## 1. 🏗️ Executive Summary & Architecture Overview

The platform implements a **Hybrid / Lambda Architecture** tailored for high-throughput Industrial IoT (IIoT) and discrete manufacturing environments. It decouples high-velocity streaming ingestion from compute-heavy historical aggregations while delivering sub-second anomaly detection and near real-time operational visibility.

```
+-------------------------------------------------------------------------------------------------------+
|                                         INGESTION LAYER                                               |
|       simulator.py (Simulates PLC / Edge Telemetry: Status Codes, Cycle Times, Good/Defect Counts)    |
+---------------------------------------------------+---------------------------------------------------+
                                                    | (Streaming Event Ingestion)
                                                    v
+-------------------------------------------------------------------------------------------------------+
|                                     STORAGE LAYER (PostgreSQL 15)                                     |
|                                                                                                       |
|       [Raw Telemetry Table]                                   [Master Reference Table]                |
|       machine_telemetry (Partition/Index by TS & Line)        downtime_reasons (Status Categories)    |
+-------------------+---------------------------------------------------------------+-------------------+
                    |                                                               |
     (Real-Time Polling / Watermark)                                 (Scheduled Hourly Batch Window)
                    |                                                               |
                    v                                                               v
+---------------------------------------+                       +---------------------------------------+
|              SPEED LAYER              |                       |              BATCH LAYER              |
|   stream_monitor.py                   |                       |   batch_etl.py (Idempotent Upsert)    |
|   - Physical Data Quality Gate        |                       |   scheduler.py (Periodic Automation)  |
|   - Critical Breakdown Detection      |                       +-------------------+-------------------+
|   - Stateful Consecutive Defect Spike |                                           | (Hourly Aggregation)
|     Tracking (In-Memory Streak >= 2)  |                                           v
+---------------------------------------+                       +---------------------------------------+
                    |                                           |               DATA MART               |
                    |                                           |   hourly_production_summary           |
                    |                                           |   (A, P, Q, OEE per Line/Machine)     |
                    |                                           +-------------------+-------------------+
                    |                                                               |
                    +-------------------------------+-------------------------------+
                                                    |
                                                    v
+-------------------------------------------------------------------------------------------------------+
|                                     SERVING & VISUALIZATION LAYER                                     |
|   dashboard.py (Containerized Streamlit Multi-Service UI @ Port 8501)                                 |
|   - Live Machine Health Cards (Dynamic Category Indicators & Good/Defect Deltas)                      |
|   - Real-Time Telemetry Feed (Auto-refresh every 3 seconds via streamlit-autorefresh)                 |
|   - Historic OEE Trend & Performance Analytics (Plotly Express)                                       |
+-------------------------------------------------------------------------------------------------------+
```

### Component Responsibility Matrix
* **Ingestion Layer:** Event-driven telemetry stream simulator ([`simulator.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/simulator.py)) emulating multi-machine PLC outputs.
* **Storage Layer:** Relational ACID storage using PostgreSQL 15 with Docker persistent volume mapping ([`init_db.sql`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/init_db.sql)).
* **Speed Layer:** Stateful stream monitor ([`stream_monitor.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/stream_monitor.py)) providing zero-lag anomaly escalation and data validation.
* **Batch Layer:** Production ETL orchestrator ([`batch_etl.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/batch_etl.py)) and lightweight scheduler ([`scheduler.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/scheduler.py)) aggregating raw signals into dimensional marts.
* **Serving Layer:** Interactive BI Dashboard ([`dashboard.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/dashboard.py)) running in a dedicated Docker service ([`Dockerfile`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/Dockerfile)).

---

## 2. ⚙️ Tech Stack & Engineering Standards

### Core Technologies
* **Runtime & Language:** Python 3.11+
* **Analytics & Visualization:** Streamlit, Plotly Express, `streamlit-autorefresh`
* **Database & ORM:** PostgreSQL 15, SQLAlchemy 2.0+, Psycopg2-binary
* **Containerization & Orchestration:** Docker, Docker Compose (Multi-Service Architecture: `mfg_postgres`, `mfg_dashboard`)
* **Task Scheduling:** Python `schedule` engine

### Enterprise Production Patterns
1. **Idempotent Upsert Strategy:**
   * Uses `INSERT INTO hourly_production_summary ... ON CONFLICT (hour_bucket, line_id, machine_id) DO UPDATE` to guarantee that batch pipeline re-runs are non-destructive, deterministic, and prevent duplicate KPI entries.
2. **Stateful In-Memory Stream Processing:**
   * Utilizes `collections.defaultdict(int)` keyed by `"{line_id}_{machine_id}"` for sub-millisecond streak tracking without incurring continuous database write overhead.
3. **Data Quality Gates (DQG):**
   * Drops and flags anomalous sensor signals (e.g. non-positive or `NULL` cycle times: $t \le 0$) prior to downstream KPI computation.
4. **Execution Auditing & Observability:**
   * Every batch run records execution metadata in [`pipeline_execution_logs`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/create_logs_table.sql) capturing start/end timestamps, duration, processed row counts, status (`SUCCESS` / `FAILED`), and full error tracebacks.
5. **Graceful Shutdown & Resilience:**
   * Handles OS signals and `KeyboardInterrupt` cleanly, ensuring active database connections, transactions, and cursor allocations are released.

---

## 3. 📐 Schema Design & Metric Definitions

### Database Schema Overview

```
 +-----------------------------------+          +-----------------------------------+
 |         downtime_reasons          |          |         machine_telemetry         |
 +-----------------------------------+          +-----------------------------------+
 | PK  status_code      INT          |<----+    | PK  event_id        BIGSERIAL     |
 |     status_name      VARCHAR(50)  |     +--- | FK  status_code     INT           |
 |     category         VARCHAR(30)  |          |     line_id         VARCHAR(20)   |
 +-----------------------------------+          |     machine_id      VARCHAR(20)   |
                                                |     timestamp       TIMESTAMPTZ   |
 +-----------------------------------+          |     cycle_time_sec  NUMERIC(6,2)  |
 |     hourly_production_summary     |          |     good_units      INT           |
 +-----------------------------------+          |     defect_units    INT           |
 | PK  summary_id       SERIAL       |          +-----------------------------------+
 | UK  hour_bucket      TIMESTAMP    |
 | UK  line_id          VARCHAR(50)  |          +-----------------------------------+
 | UK  machine_id       VARCHAR(50)  |          |      pipeline_execution_logs      |
 |     total_cycles     INT          |          +-----------------------------------+
 |     total_good_units INT          |          | PK  log_id          SERIAL        |
 |     total_defect_u   INT          |          |     pipeline_name   VARCHAR(100)  |
 |     operating_time_s NUMERIC(10,2)|          |     start_time      TIMESTAMP     |
 |     unplanned_dt_s   NUMERIC(10,2)|          |     end_time        TIMESTAMP     |
 |     availability_pct NUMERIC(5,2) |          |     status          VARCHAR(20)   |
 |     performance_pct  NUMERIC(5,2) |          |     rows_processed  INT           |
 |     quality_pct      NUMERIC(5,2) |          |     error_message   TEXT          |
 |     oee_pct          NUMERIC(5,2) |          |     created_at      TIMESTAMP     |
 +-----------------------------------+          +-----------------------------------+
```

### Table Specifications

#### 1. `machine_telemetry` (Raw Ingestion Layer)
* Stores high-frequency raw telemetry events from line PLCs.
* Indexed by `(timestamp)` and `(line_id, machine_id)` for high-throughput temporal scanning.

#### 2. `downtime_reasons` (Master Reference Dimension)
* Categorizes status codes into `Production`, `Planned Maintenance`, `Unplanned Downtime`, and `Idle`.

#### 3. `hourly_production_summary` (Aggregated Data Mart)
* Stores calculated 3-pillar OEE metrics aggregated per hour window.
* Enforces `UNIQUE(hour_bucket, line_id, machine_id)` for idempotent upserts.

#### 4. `pipeline_execution_logs` (Audit Trail)
* Maintains pipeline observability, audit logs, affected row metrics, and error stack traces.

---

### 📊 OEE Mathematical Model

Overall Equipment Effectiveness (OEE) evaluates manufacturing productivity through three distinct dimensions:

$$OEE = \text{Availability} \times \text{Performance} \times \text{Quality}$$

$$\text{OEE (\%)} = \frac{\text{Availability (\%)} \times \text{Performance (\%)} \times \text{Quality (\%)}}{10000}$$

| OEE Pillar | Mathematical Definition | SQL Operational Formula | Description |
| :--- | :--- | :--- | :--- |
| **Availability ($A$)** | $\frac{\text{Run Time}}{\text{Planned Production Time}} \times 100$ | $\frac{\text{Operating Time}}{\text{Operating Time} + \text{Unplanned Downtime}} \times 100$ | Measures proportion of planned operating time without machine breakdown. |
| **Performance ($P$)** | $\frac{\text{Ideal Operating Time}}{\text{Actual Operating Time}} \times 100$ | $\min\left(\frac{\text{Ideal Cycle Time} \times \text{Total Produced Units}}{\text{Operating Time}} \times 100,\, 100\right)$ | Measures production speed efficiency against designed ideal cycle speed. |
| **Quality ($Q$)** | $\frac{\text{Good Units}}{\text{Total Units Produced}} \times 100$ | $\frac{\text{Total Good Units}}{\text{Total Good Units} + \text{Total Defect Units}} \times 100$ | Measures first-pass manufacturing yield and defect-free output. |

#### Machine Ideal Cycle Times (Engineered Standards)
* **`CNC_A`:** $12.0\text{ seconds/unit}$
* **`CNC_B`:** $15.0\text{ seconds/unit}$
* **`ROBOT_ARM`:** $8.0\text{ seconds/unit}$
* **Standard Baseline:** $10.0\text{ seconds/unit}$

---

## 🗓️ Key Milestones Completed (Weeks 1 - 4)

### Week 1: Data Modeling & Synthetic PLC Telemetry Simulation
* Designed schema architecture across raw telemetry and downtime master tables.
* Deployed containerized PostgreSQL 15 environment with volume persistence.
* Built synthetic PLC stream generator ([`simulator.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/simulator.py)) emulating realistic machine states (80% normal production, 20% breakdown/idle/tool change).
* Authored core SQL OEE aggregation CTEs ([`populate_datamart.sql`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/populate_datamart.sql)).

### Week 2: Automated Batch ETL & Orchestration
* Implemented production-grade Python ETL pipeline ([`batch_etl.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/batch_etl.py)) using SQLAlchemy 2.0.
* Integrated idempotent `ON CONFLICT DO UPDATE` upsert logic to support non-blocking pipeline re-runs.
* Built automated execution logging table ([`create_logs_table.sql`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/create_logs_table.sql)) for end-to-end auditability.
* Configured automated periodic batch execution scheduler ([`scheduler.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/scheduler.py)).

### Week 3: Stateful Real-Time Stream Monitoring & Anomaly Detection
* Developed real-time stream monitor ([`stream_monitor.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/stream_monitor.py)) using watermark-based incremental polling (`MAX(event_id)`).
* Implemented **Data Quality Gate** to intercept invalid or poisoned cycle times ($t \le 0$).
* Engineered stateful in-memory quality tracking with `defaultdict` to detect **Consecutive Defect Spikes** ($\ge 2$ consecutive defect events) with automatic recovery reset.
* Configured real-time color-coded ANSI incident severity alerting (Critical Breakdown vs. Defect Spike vs. Healthy).

### Week 4: Multi-Container Dockerization & Real-Time BI Dashboard
* Containerized Python application layer with multi-stage [`Dockerfile`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/Dockerfile).
* Configured multi-service orchestration via [`docker-compose.yml`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/docker-compose.yml) connecting `mfg_postgres` and `mfg_dashboard` across an isolated Docker network.
* Built interactive real-time manufacturing dashboard ([`dashboard.py`](file:///c:/Users/Acer/Downloads/All%20Project/mfg-data-pipeline/dashboard.py)) featuring:
  - Dynamic KPI status cards with delta metrics and health status colors.
  - 3-second live auto-refresh feed powered by `streamlit-autorefresh`.
  - Historical OEE trend visualization across machines using Plotly Express.

---

## 🚀 Quick Start & Deployment Guide (Zero to Running)

### 1. Multi-Container Deployment via Docker Compose

Clone repository and spin up all platform services in detached mode:

```powershell
# Build and start all containers (PostgreSQL & Streamlit Dashboard)
docker compose up --build -d

# Verify container health and networking status
docker compose ps
```

* 🌐 **Real-Time Streamlit Dashboard:** Open browser at [http://localhost:8501](http://localhost:8501)
* 🗄️ **PostgreSQL Port:** Exposed on `localhost:5432` (User: `mfg_user`, Database: `manufacturing_db`)

---

### 2. Local Environment Setup & Database Initialization

If running ingestion or monitoring scripts locally outside Docker:

```powershell
# 1. Create and activate Python Virtual Environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install all platform dependencies
pip install -r requirements.txt
```

#### Schema Initialization (First-Time Setup):
```powershell
# 1. Initialize Base Schema & Master Tables
Get-Content init_db.sql | docker exec -i mfg_postgres psql -U mfg_user -d manufacturing_db

# 2. Initialize Data Mart Table & Indexes
Get-Content create_datamart.sql | docker exec -i mfg_postgres psql -U mfg_user -d manufacturing_db

# 3. Initialize Pipeline Audit Logs Table
Get-Content create_logs_table.sql | docker exec -i mfg_postgres psql -U mfg_user -d manufacturing_db
```

---

### 3. Running Data Platform Workflows

#### Step A: Start Real-Time Ingestion Simulator
Start streaming synthetic PLC telemetry events (Terminal 1):
```powershell
.\.venv\Scripts\python simulator.py
```
*(Generates events every 2 seconds; press `Ctrl+C` to stop)*

#### Step B: Start Stateful Stream Monitor & Anomaly Detector
Monitor live events and trigger real-time quality/breakdown alerts (Terminal 2):
```powershell
.\.venv\Scripts\python stream_monitor.py
```

#### Step C: Run Automated Batch ETL Scheduler
Automate recurring 1-minute OEE Data Mart calculations and audit logging (Terminal 3):
```powershell
.\.venv\Scripts\python scheduler.py
```

#### Step D: Ad-Hoc Batch Execution & CLI KPI Reporting
```powershell
# Run a single manual Batch ETL cycle
.\.venv\Scripts\python batch_etl.py

# Print multi-level terminal OEE analytics report
.\.venv\Scripts\python run_analysis.py
```

---

### 4. Direct Database Inspection & Observability

Access the PostgreSQL database CLI inside Docker:
```powershell
docker exec -it mfg_postgres psql -U mfg_user -d manufacturing_db
```

```sql
-- 1. Inspect Data Mart OEE aggregations
SELECT hour_bucket, line_id, machine_id, total_produced_units, availability_pct, performance_pct, quality_pct, oee_pct 
FROM hourly_production_summary 
ORDER BY hour_bucket DESC, line_id, machine_id;

-- 2. Check Pipeline Execution Audit Logs
SELECT log_id, pipeline_name, start_time, end_time, status, rows_processed, error_message 
FROM pipeline_execution_logs 
ORDER BY log_id DESC 
LIMIT 10;

-- 3. Check Live Machine Telemetry Event Counts
SELECT line_id, machine_id, COUNT(*) AS event_count, SUM(good_units) AS good, SUM(defect_units) AS defect 
FROM machine_telemetry 
GROUP BY line_id, machine_id;
```

---

### 5. Service Teardown & Maintenance

```powershell
# Stop all services (preserves database volume data)
docker compose stop

# Stop and remove containers and network
docker compose down

# Full reset: Wipe containers, network, and persistent storage volumes
docker compose down -v
```