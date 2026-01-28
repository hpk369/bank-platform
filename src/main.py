#!/usr/bin/env python3
"""
Banking Platform - Main Orchestration Script
Runs the complete transaction processing pipeline
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transaction_generator import TransactionGenerator
from fraud_detector import FraudDetector
from analytics import TransactionAnalytics
from monitor import SystemMonitor

def print_banner(text):
    """Print formatted banner"""
    print(f"\n{'='*70}")
    print(f"{text:^70}")
    print(f"{'='*70}\n")

def main():
    """Main pipeline orchestration"""
    
    print_banner("BANKING TRANSACTION PROCESSING PLATFORM")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: System Health Check
    print_banner("STEP 1: System Health Check")
    monitor = SystemMonitor()
    health_report = monitor.generate_health_report()
    monitor.print_report(health_report)
    
    if health_report['overall_status'] == 'CRITICAL':
        print("\n❌ CRITICAL system issues detected. Please resolve before proceeding.")
        return
    
    # Step 2: Generate Transactions
    print_banner("STEP 2: Generate Sample Transactions")
    generator = TransactionGenerator(num_accounts=500)
    print("Generating 10,000 banking transactions...")
    transactions = generator.generate_batch(10000)
    
    data_file = '../data/sample_transactions.json'
    generator.save_to_file(transactions, data_file)
    print(f"✅ Generated and saved {len(transactions):,} transactions")
    
    # Show sample
    print("\nSample transaction:")
    print(f"  ID: {transactions[0]['transaction_id']}")
    print(f"  Type: {transactions[0]['transaction_type']}")
    print(f"  Amount: ${transactions[0]['amount']:.2f}")
    print(f"  Location: {transactions[0]['location']}")
    
    # Step 3: Fraud Detection
    print_banner("STEP 3: Real-Time Fraud Detection")
    detector = FraudDetector()
    print(f"Processing {len(transactions):,} transactions through fraud detection...")
    
    fraud_alerts = []
    for txn in transactions:
        alerts = detector.process_transaction(txn)
        fraud_alerts.extend(alerts)
    
    fraud_summary = detector.get_fraud_summary()
    print(f"\n✅ Fraud detection complete")
    print(f"  Total alerts: {fraud_summary['total_alerts']}")
    
    if fraud_summary.get('by_type'):
        print(f"  Alert breakdown:")
        for alert_type, count in fraud_summary['by_type'].items():
            print(f"    - {alert_type}: {count}")
    
    # Step 4: Analytics
    print_banner("STEP 4: Transaction Analytics")
    analytics = TransactionAnalytics()
    analytics.load_transactions(data_file)
    
    print("Generating comprehensive analytics report...")
    report = analytics.generate_report('../data/analytics_report.json')
    
    summary = report['daily_summary']
    print(f"\n✅ Analytics complete")
    print(f"  Total transactions: {summary['total_transactions']:,}")
    print(f"  Total volume: ${summary['total_volume']:,.2f}")
    print(f"  Transaction types:")
    for txn_type, count in summary['by_type'].items():
        print(f"    - {txn_type}: {count:,}")
    
    # Step 5: Summary
    print_banner("PIPELINE EXECUTION SUMMARY")
    print(f"✅ All steps completed successfully!")
    print(f"\nGenerated files:")
    print(f"  📄 sample_transactions.json ({len(transactions):,} transactions)")
    print(f"  📄 analytics_report.json")
    print(f"  📄 health_report.json")
    
    print(f"\nKey Metrics:")
    print(f"  💰 Total transaction volume: ${summary['total_volume']:,.2f}")
    print(f"  🚨 Fraud alerts detected: {fraud_summary['total_alerts']}")
    print(f"  ✅ Completed transactions: {summary['by_status'].get('COMPLETED', 0):,}")
    print(f"  ❌ Failed transactions: {summary['by_status'].get('FAILED', 0):,}")
    
    print(f"\n{'='*70}")
    print(f"Pipeline completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
