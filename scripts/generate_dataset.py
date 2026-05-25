#!/usr/bin/env python3
"""
Generates a synthetic PaySim-style banking fraud dataset.
Produces ~200K transactions with realistic fraud patterns.

Output: data/transactions_demo.csv.gz
"""

import csv
import gzip
import os
import random
import uuid
from datetime import datetime, timedelta

TOTAL_ROWS = 200_000
FRAUD_RATE_TRANSFER = 0.08   # 8% of TRANSFER are fraud
FRAUD_RATE_CASHOUT  = 0.04   # 4% of CASH_OUT are fraud

TYPE_WEIGHTS = {
    "PAYMENT":  0.34,
    "CASH_OUT": 0.35,
    "CASH_IN":  0.14,
    "DEBIT":    0.09,
    "TRANSFER": 0.08,
}

TYPES = list(TYPE_WEIGHTS.keys())
WEIGHTS = list(TYPE_WEIGHTS.values())

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
    "Indianapolis", "Seattle", "Denver", "Washington", "Nashville",
]

MERCHANTS = [
    "Amazon", "Walmart", "Target", "Costco", "Home Depot",
    "Best Buy", "Kroger", "CVS", "Walgreens", "McDonald's",
    "Starbucks", "Apple", "Netflix", "Uber", "Airbnb",
    "Shell", "BP", "Chase ATM", "Wells Fargo ATM", "Bank Transfer",
]

NUM_ACCOUNTS = 8_000

def rand_account(prefix="C"):
    n = random.randint(1_000_000, 9_999_999)
    return f"{prefix}{n}"


def rand_amount(txn_type, is_fraud):
    if is_fraud:
        # Fraud: large amounts to drain accounts
        return round(random.uniform(150_000, 2_000_000), 2)
    if txn_type in ("TRANSFER", "CASH_OUT"):
        return round(random.lognormvariate(9.5, 1.8), 2)
    if txn_type == "CASH_IN":
        return round(random.lognormvariate(8.5, 1.5), 2)
    # PAYMENT / DEBIT — smaller everyday amounts
    return round(random.lognormvariate(5.0, 1.2), 2)


def generate():
    out_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "transactions_demo.csv.gz"
    )
    out_path = os.path.normpath(out_path)

    accounts = [rand_account("C") for _ in range(NUM_ACCOUNTS)]
    merchant_accounts = [rand_account("M") for _ in range(500)]

    start_time = datetime(2024, 1, 1, 0, 0, 0)

    print(f"Generating {TOTAL_ROWS:,} transactions → {out_path}")

    fieldnames = [
        "transaction_id", "step", "type", "amount",
        "account_orig", "old_balance_orig", "new_balance_orig",
        "account_dest", "old_balance_dest", "new_balance_dest",
        "is_fraud", "timestamp", "location", "merchant",
    ]

    balances = {acc: round(random.uniform(1_000, 500_000), 2) for acc in accounts}

    written = 0
    with gzip.open(out_path, "wt", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for step in range(1, TOTAL_ROWS + 1):
            txn_type = random.choices(TYPES, weights=WEIGHTS, k=1)[0]

            is_fraud = 0
            if txn_type == "TRANSFER" and random.random() < FRAUD_RATE_TRANSFER:
                is_fraud = 1
            elif txn_type == "CASH_OUT" and random.random() < FRAUD_RATE_CASHOUT:
                is_fraud = 1

            amount = rand_amount(txn_type, bool(is_fraud))

            orig = random.choice(accounts)
            if txn_type in ("TRANSFER", "CASH_OUT"):
                dest = random.choice(accounts)
            else:
                dest = random.choice(merchant_accounts)

            old_bal_orig = balances.get(orig, 0.0)
            new_bal_orig = max(0.0, round(old_bal_orig - amount, 2))
            if is_fraud:
                new_bal_orig = 0.0   # Fraud drains the account

            old_bal_dest = balances.get(dest, 0.0)
            new_bal_dest = round(old_bal_dest + amount, 2) if txn_type != "CASH_OUT" else old_bal_dest

            balances[orig] = new_bal_orig
            if dest in balances:
                balances[dest] = new_bal_dest

            ts = start_time + timedelta(hours=step // 10, minutes=(step % 10) * 6)

            writer.writerow({
                "transaction_id": str(uuid.uuid4()),
                "step": step,
                "type": txn_type,
                "amount": amount,
                "account_orig": orig,
                "old_balance_orig": old_bal_orig,
                "new_balance_orig": new_bal_orig,
                "account_dest": dest,
                "old_balance_dest": old_bal_dest,
                "new_balance_dest": new_bal_dest,
                "is_fraud": is_fraud,
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "location": random.choice(CITIES),
                "merchant": random.choice(MERCHANTS),
            })
            written += 1

            if written % 50_000 == 0:
                print(f"  {written:,} / {TOTAL_ROWS:,} rows written...")

    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f"Done. {written:,} rows — {size_mb:.1f} MB compressed.")


if __name__ == "__main__":
    generate()
