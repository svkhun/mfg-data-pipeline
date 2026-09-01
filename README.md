# Real-Time & Batch Manufacturing Data Pipeline

An end-to-end data pipeline simulating IoT/PLC line telemetry from industrial machines, persisting raw streaming events in PostgreSQL via Docker, and calculating key manufacturing KPIs (Defect Rate, Downtime Analysis, and OEE).

---

## Architecture Overview
- **Data Ingestion:** Event-driven telemetry stream simulator (`simulator.py`)
- **Storage Layer:** PostgreSQL 15 deployed on Docker
- **Analytics & ETL:** SQL queries and automated execution via Pandas & SQLAlchemy (`run_analysis.py`)

---

## Complete Command Guide

### 1. Project Setup & Dependencies
```powershell
# Create Virtual Environment
python -m venv .venv

# Install Required Libraries
.\.venv\Scripts\pip install psycopg2-binary pandas sqlalchemy

# Start PostgreSQL Container
docker compose up -d

# Stop Container (keep data volume)
docker compose stop

# Tear down Container and Network
docker compose down

# Step 1: Run Telemetry Ingestion Simulator (Press Ctrl+C to stop)
.\.venv\Scripts\python simulator.py

# Step 2: Run KPI Analytics & Summary Engine
.\.venv\Scripts\python run_analysis.py

# Connect directly to PostgreSQL CLI inside Docker
docker exec -it mfg_postgres psql -U mfg_user -d manufacturing_db

# Run SQL script directly from file
Get-Content analysis_kpi.sql | docker exec -i mfg_postgres psql -U mfg_user -d manufacturing_db