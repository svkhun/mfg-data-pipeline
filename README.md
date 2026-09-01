# Real-Time & Batch Manufacturing Data Pipeline

An end-to-end data pipeline simulating IoT/PLC telemetry from industrial machinery, persisting raw streaming events into PostgreSQL via Docker, and calculating operational manufacturing KPIs (Defect Rate, Downtime Analysis, and OEE).

---

## 🏗️ Architecture Overview

* **Data Ingestion:** Event-driven telemetry stream simulator (`simulator.py`)
* **Storage Layer:** PostgreSQL 15 deployed on Docker
* **Analytics & ETL Engine:** Automated metrics processing via Pandas, SQLAlchemy, and SQL scripts (`run_analysis.py`)

---

## 📊 Calculated KPIs

| KPI | Description |
| :--- | :--- |
| **Defect Rate** | Ratio of rejected parts to total production count |
| **Downtime Analysis** | Duration and classification of unplanned machine stops |
| **OEE (Overall Equipment Effectiveness)** | Product of Availability, Performance, and Quality |

---

## 🚀 Getting Started

### 1. Environment Setup

Clone the repository and prepare the Python environment:

```powershell
# Create virtual environment
python -m venv .venv

# Install dependencies
.\.venv\Scripts\pip install psycopg2-binary pandas sqlalchemy
```

---

### 2. Infrastructure Management

Manage the PostgreSQL database container via Docker Compose:

```powershell
# Start database container in background
docker compose up -d

# Stop container (preserves data volumes)
docker compose stop

# Tear down container and network
docker compose down
```

---

### 3. Pipeline Execution

Run the pipeline sequentially to stream data and calculate analytics:

```powershell
# Step 1: Run telemetry ingestion simulator (Press Ctrl+C to stop)
.\.venv\Scripts\python simulator.py

# Step 2: Run KPI analytics and summary engine
.\.venv\Scripts\python run_analysis.py
```

---

## 🛠️ Database Operations & Direct Querying

Useful CLI commands for debugging and manual data inspection:

```powershell
# Open interactive PostgreSQL CLI inside Docker
docker exec -it mfg_postgres psql -U mfg_user -d manufacturing_db

# Execute a local SQL script directly
Get-Content analysis_kpi.sql | docker exec -i mfg_postgres psql -U mfg_user -d manufacturing_db
```