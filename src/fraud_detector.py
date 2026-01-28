#!/usr/bin/env python3
"""
Fraud Detection System
Real-time fraud pattern detection for banking transactions
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict

class FraudDetector:
    """Detect fraudulent transaction patterns"""
    
    def __init__(self):
        self.account_history = defaultdict(list)
        self.fraud_alerts = []
        self.HIGH_AMOUNT_THRESHOLD = 5000
        self.VELOCITY_THRESHOLD = 5
        self.VELOCITY_WINDOW = 300
        self.UNUSUAL_LOCATION_THRESHOLD = 3
    
    def check_high_amount(self, transaction):
        """Flag unusually high transactions"""
        if transaction['amount'] > self.HIGH_AMOUNT_THRESHOLD:
            return {
                'alert_type': 'HIGH_AMOUNT',
                'severity': 'HIGH',
                'reason': f"Amount ${transaction['amount']} exceeds ${self.HIGH_AMOUNT_THRESHOLD}",
                'transaction_id': transaction['transaction_id']
            }
        return None
    
    def check_velocity(self, transaction):
        """Flag rapid succession of transactions"""
        account = transaction['account_number']
        current_time = datetime.strptime(transaction['timestamp'], '%Y-%m-%d %H:%M:%S')
        
        recent_txns = [
            txn for txn in self.account_history[account]
            if (current_time - datetime.strptime(txn['timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds() <= self.VELOCITY_WINDOW
        ]
        
        if len(recent_txns) >= self.VELOCITY_THRESHOLD:
            return {
                'alert_type': 'VELOCITY',
                'severity': 'MEDIUM',
                'reason': f"{len(recent_txns)} transactions in {self.VELOCITY_WINDOW}s",
                'transaction_id': transaction['transaction_id']
            }
        return None
    
    def process_transaction(self, transaction):
        """Process a transaction through all fraud checks"""
        account = transaction['account_number']
        alerts = []
        
        checks = [
            self.check_high_amount(transaction),
            self.check_velocity(transaction)
        ]
        
        for alert in checks:
            if alert:
                alert['account_number'] = account
                alert['timestamp'] = transaction['timestamp']
                alerts.append(alert)
                self.fraud_alerts.append(alert)
        
        self.account_history[account].append(transaction)
        
        if len(self.account_history[account]) > 100:
            self.account_history[account] = self.account_history[account][-100:]
        
        return alerts
    
    def get_fraud_summary(self):
        """Get summary of fraud alerts"""
        if not self.fraud_alerts:
            return {"total_alerts": 0}
        
        summary = {
            'total_alerts': len(self.fraud_alerts),
            'by_type': defaultdict(int),
            'by_severity': defaultdict(int)
        }
        
        for alert in self.fraud_alerts:
            summary['by_type'][alert['alert_type']] += 1
            summary['by_severity'][alert['severity']] += 1
        
        return dict(summary)

if __name__ == '__main__':
    detector = FraudDetector()
    print("Loading transactions for fraud detection...")
    
    with open('../data/sample_transactions.json', 'r') as f:
        transactions = [json.loads(line) for line in f]
    
    print(f"Processing {len(transactions)} transactions...")
    
    fraud_count = 0
    for txn in transactions:
        alerts = detector.process_transaction(txn)
        if alerts:
            fraud_count += 1
            if fraud_count <= 5:
                print(f"\n🚨 FRAUD ALERT for {txn['transaction_id']}:")
                for alert in alerts:
                    print(f"  - {alert['alert_type']}: {alert['reason']}")
    
    summary = detector.get_fraud_summary()
    print(f"\n{'='*50}")
    print("FRAUD DETECTION SUMMARY")
    print(f"{'='*50}")
    print(f"Total transactions processed: {len(transactions)}")
    print(f"Total fraud alerts: {summary['total_alerts']}")
    print(f"\nAlerts by type:")
    for alert_type, count in summary.get('by_type', {}).items():
        print(f"  {alert_type}: {count}")
