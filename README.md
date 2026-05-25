# Banking Transaction Processing Platform

> **Real-time fraud detection pipeline demonstrating the evolution from batch file processing to distributed Spark Streaming — built to production-grade architecture standards.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-%E2%86%92%20Open%20Dashboard-blue?style=for-the-badge)](https://hpk369.github.io/bank-platform/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=flat-square&logo=apachekafka)](https://kafka.apache.org)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-E25A1C?style=flat-square&logo=apachespark&logoColor=white)](https://spark.apache.org)

---

## 🚀 Live Demo

**[→ https://hpk369.github.io/bank-platform/](https://hpk369.github.io/bank-platform/)**

Streams 200,000 synthetic banking transactions through real-time fraud detection in the browser — no setup required. Runs the full pipeline locally with FastAPI + WebSocket when the backend is available, or falls back to a built-in JavaScript simulator.

---

## Overview

This project models the **three-stage data engineering evolution** commonly seen in production banking systems:

| Stage | Technology | Throughput | Use Case |
|-------|-----------|------------|----------|
| **1. File Mode** | Python + JSON | ~1,000 txn/s | Prototyping & learning |
| **2. Kafka Mode** | Apache Kafka | ~10,000 txn/s | Microservices & real-time |
| **3. Spark Streaming** | Spark + Kafka | 33,000+ txn/s | Distributed production scale |

The same fraud detection logic runs across all three modes, making the architectural trade-offs concrete and measurable.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  FILE MODE (Baseline)                                           │
│  Transaction Generator → JSON File → Fraud Detector → Report   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  KAFKA MODE (Real-Time)                                         │
│  Generator ──► [banking-transactions] ──► Fraud Detector        │
│                      Kafka Topic              │                 │
│                                          [fraud-alerts]         │
│                                          Kafka Topic            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  SPARK STREAMING MODE (Production)                              │
│  Generator ──► Kafka ──► Spark Structured Streaming             │
│                              │  (distributed across cluster)    │
│                         ┌────┴────┐                             │
│                    [fraud-alerts] [processed-transactions]      │
│                         Kafka Topics → Analytics                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Stream Processing** | Apache Spark Structured Streaming (PySpark) |
| **Message Broker** | Apache Kafka (Producer/Consumer) |
| **API Server** | FastAPI + WebSocket (asyncio) |
| **Dataset** | Synthetic PaySim-style — 200K transactions, 11 MB |
| **Dashboard** | Vanilla JS + Chart.js (WebSocket / browser simulator) |
| **CI/CD** | GitHub Actions → GitHub Pages |
| **Language** | Python 3.10+ |

---

## Fraud Detection Rules

Four rules run on every transaction, identical across all three pipeline modes:

| Rule | Logic | Severity |
|------|-------|----------|
| `HIGH_AMOUNT` | Any transaction > $200,000 | High |
| `BALANCE_DRAIN` | TRANSFER/CASH_OUT leaves origin balance at $0 | Critical |
| `TRANSFER_SPIKE` | TRANSFER with amount > $150,000 | High |
| `DATASET_FRAUD` | Labelled fraud in source dataset | Critical |

---

## Project Structure

```
bank-platform/
├── src/
│   ├── api_server.py               # FastAPI + WebSocket streaming server
│   ├── demo_streamer.py            # Replays dataset through fraud rules (80 rows/s)
│   ├── fraud_detector_spark.py     # PySpark Structured Streaming job
│   ├── fraud_detector_kafka.py     # Kafka consumer/producer fraud detector
│   ├── fraud_detector.py           # File-mode fraud detector (baseline)
│   ├── transaction_generator.py    # File-mode transaction generator
│   ├── transaction_generator_kafka.py  # Kafka-enabled generator
│   ├── analytics.py                # Batch analytics engine
│   ├── monitor.py                  # System health monitoring
│   ├── main.py                     # File-mode pipeline entry point
│   └── config.py                   # Kafka, Spark, and app configuration
├── frontend/
│   ├── index.html                  # Dashboard layout
│   ├── app.js                      # WebSocket client + browser simulator
│   └── style.css                   # Dark theme dashboard styles
├── data/
│   └── transactions_demo.csv.gz    # 200K synthetic transactions (11 MB)
├── scripts/
│   ├── start_demo.sh               # One-command demo startup
│   ├── generate_dataset.py         # Regenerate dataset at any scale
│   ├── run_pipeline.sh             # Full pipeline runner
│   └── health_check.sh             # Service health checks
├── docs/
│   ├── THREE_MODES_COMPARISON.md
│   └── RESUME_SUMMARY.md
├── .github/workflows/
│   └── pages.yml                   # Auto-deploy dashboard to GitHub Pages
├── KAFKA_SPARK_GUIDE.md            # Full Kafka + Spark setup guide
├── requirements.txt                # File-mode dependencies
├── requirements-kafka-spark.txt    # Kafka + Spark dependencies
└── requirements-demo.txt           # Demo server dependencies
```

---

## Quick Start

### Option 1 — Live Demo (no setup)
Open **[https://hpk369.github.io/bank-platform/](https://hpk369.github.io/bank-platform/)** in any browser.

### Option 2 — Run Locally (full backend)

```bash
# Clone and start
git clone https://github.com/hpk369/bank-platform.git
cd bank-platform
bash scripts/start_demo.sh
# Open http://localhost:8000
```

The startup script installs dependencies and generates the dataset automatically on first run.

### Option 3 — Kafka Mode

```bash
pip install -r requirements-kafka-spark.txt

# Terminal 1 — generate a stream of transactions
python3 src/transaction_generator_kafka.py --kafka --stream --count 1000

# Terminal 2 — run fraud detection
python3 src/fraud_detector_kafka.py --kafka --max 1000
```

### Option 4 — Spark Structured Streaming

```bash
pip install -r requirements-kafka-spark.txt

# Stream from Kafka, output to console
python3 src/fraud_detector_spark.py --stream --console

# Or run batch analysis on a file
python3 src/fraud_detector_spark.py --batch data/transactions_demo.csv.gz
```

---

## Dashboard Features

The live dashboard visualises the streaming pipeline in real time:

- **Stat cards** — transactions/sec, total processed, fraud count, fraud rate, batch number, uptime
- **Live transaction feed** — scrolling table with fraud rows highlighted, capped at 80 visible rows
- **Fraud alerts panel** — each alert shows amount, triggered rules, account, location, and timestamp
- **Throughput chart** — line chart of rows/sec over the last 40 batches
- **Transaction type chart** — doughnut showing PAYMENT / CASH\_OUT / CASH\_IN / DEBIT / TRANSFER split
- **Fraud rule breakdown** — bar chart of detections per rule
- **Spark status bar** — batch counter, checkpoint path, source file

---

## Configuration

Edit `src/config.py` to tune the pipeline:

```python
# Fraud detection thresholds
APP_CONFIG = {
    'fraud_thresholds': {
        'high_amount': 5000,       # Flag transactions above this amount
        'velocity_count': 5,       # Flag if N+ transactions in window
        'velocity_window': 300,    # Window size in seconds (5 min)
    }
}

# Kafka broker and topic names
KAFKA_CONFIG = {
    'bootstrap_servers': ['localhost:9092'],
    'topics': {
        'transactions':  'banking-transactions',
        'fraud_alerts':  'fraud-alerts',
        'processed':     'processed-transactions',
    }
}

# Spark cluster settings
SPARK_CONFIG = {
    'master': 'local[*]',          # Use 'yarn' for cluster mode
    'executor_memory': '2g',
    'driver_memory': '2g',
}
```

---

## Performance Comparison

| Metric | File Mode | Kafka Mode | Spark Streaming |
|--------|-----------|------------|-----------------|
| **Throughput** | ~1,000 txn/s | ~10,000 txn/s | 33,000+ txn/s |
| **Latency** | Batch only | < 100 ms | < 5 s |
| **Max Volume** | 10K | 100K | Millions |
| **Fault Tolerance** | None | Kafka replication | Checkpointing + WAL |
| **Scalability** | Single machine | Horizontal | Distributed cluster |
| **Production Ready** | No | Partial | Yes |

---

## Skills Demonstrated

| Area | Detail |
|------|--------|
| **Distributed Systems** | Kafka producer/consumer patterns; Spark cluster mode |
| **Stream Processing** | Spark Structured Streaming; windowed aggregations; watermarking |
| **API Design** | FastAPI async server; WebSocket broadcast to multiple clients |
| **Data Engineering** | Schema design; PaySim-style synthetic data generation |
| **Frontend** | Real-time Chart.js dashboard; WebSocket client with fallback |
| **DevOps** | GitHub Actions CI/CD; automated GitHub Pages deployment |
| **Software Design** | Single codebase, three swappable processing modes |

---

## Roadmap

- [ ] Deploy on Hadoop cluster (HDFS + YARN)
- [ ] Add Oozie for workflow scheduling
- [ ] Grafana + Prometheus monitoring dashboards
- [ ] PagerDuty / Slack alerting integration
- [ ] Authentication and role-based access control
- [ ] Kubernetes deployment manifests
