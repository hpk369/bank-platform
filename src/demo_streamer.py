#!/usr/bin/env python3
"""
Streams the generated dataset through fraud detection rules.
Designed to feed api_server.py via an asyncio queue.

Fraud rules applied (mirrors what Spark Structured Streaming would do):
  1. HIGH_AMOUNT      — any transaction > $200K
  2. BALANCE_DRAIN    — origin balance hits 0 after TRANSFER or CASH_OUT > $10K
  3. TRANSFER_SPIKE   — TRANSFER with amount > $150K
  4. DATASET_LABEL    — rows already marked is_fraud=1 in the CSV
"""

import asyncio
import csv
import gzip
import os
import time

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "transactions_demo.csv.gz")
DATA_FILE = os.path.normpath(DATA_FILE)

ROWS_PER_SECOND = 80   # Simulated ingestion rate
BATCH_SIZE = 20        # Transactions per WebSocket push


def _fraud_rules(row: dict) -> list[str]:
    alerts = []
    amount = float(row["amount"])
    txn_type = row["type"]
    new_bal = float(row["new_balance_orig"])

    if amount > 200_000:
        alerts.append("HIGH_AMOUNT")
    if txn_type in ("TRANSFER", "CASH_OUT") and new_bal == 0 and amount > 10_000:
        alerts.append("BALANCE_DRAIN")
    if txn_type == "TRANSFER" and amount > 150_000:
        alerts.append("TRANSFER_SPIKE")
    if int(row["is_fraud"]) == 1:
        alerts.append("DATASET_FRAUD")

    return alerts


async def stream_to_queue(queue: asyncio.Queue, stop_event: asyncio.Event):
    """
    Reads the dataset in a loop, applies fraud rules, and pushes batches to queue.
    Runs until stop_event is set.
    """
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}\n"
            "Run:  python scripts/generate_dataset.py"
        )

    delay = BATCH_SIZE / ROWS_PER_SECOND  # seconds to wait between batches

    stats = {
        "total_processed": 0,
        "total_fraud": 0,
        "batches": 0,
        "start_time": time.time(),
        "rule_counts": {"HIGH_AMOUNT": 0, "BALANCE_DRAIN": 0, "TRANSFER_SPIKE": 0, "DATASET_FRAUD": 0},
    }

    while not stop_event.is_set():
        with gzip.open(DATA_FILE, "rt", newline="") as f:
            reader = csv.DictReader(f)
            batch_txns = []
            batch_alerts = []

            for row in reader:
                if stop_event.is_set():
                    break

                rules = _fraud_rules(row)
                enriched = {**row, "fraud_rules": rules, "is_flagged": len(rules) > 0}
                batch_txns.append(enriched)

                if rules:
                    batch_alerts.append(enriched)
                    stats["total_fraud"] += 1
                    for r in rules:
                        stats["rule_counts"][r] = stats["rule_counts"].get(r, 0) + 1

                stats["total_processed"] += 1

                if len(batch_txns) >= BATCH_SIZE:
                    elapsed = time.time() - stats["start_time"]
                    payload = {
                        "type": "batch",
                        "transactions": batch_txns,
                        "alerts": batch_alerts,
                        "stats": {
                            **stats,
                            "elapsed_seconds": round(elapsed, 1),
                            "rows_per_second": round(stats["total_processed"] / max(elapsed, 1), 1),
                            "fraud_rate": round(
                                stats["total_fraud"] / max(stats["total_processed"], 1) * 100, 2
                            ),
                        },
                    }
                    await queue.put(payload)
                    stats["batches"] += 1
                    batch_txns = []
                    batch_alerts = []
                    await asyncio.sleep(delay)
