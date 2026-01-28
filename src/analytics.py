#!/usr/bin/env python3
"""
Transaction Analytics and Reporting
Batch processing for daily summaries and insights
"""

import json
from collections import defaultdict
from datetime import datetime

class TransactionAnalytics:
    """Analyze transaction data and generate reports"""
    
    def __init__(self):
        self.transactions = []
    
    def load_transactions(self, filename):
        """Load transactions from file"""
        with open(filename, 'r') as f:
            self.transactions = [json.loads(line) for line in f]
        print(f"Loaded {len(self.transactions)} transactions")
    
    def daily_summary(self):
        """Generate daily transaction summary"""
        summary = {
            'total_transactions': len(self.transactions),
            'by_type': defaultdict(int),
            'by_status': defaultdict(int),
            'total_volume': 0,
            'by_type_volume': defaultdict(float)
        }
        
        for txn in self.transactions:
            summary['by_type'][txn['transaction_type']] += 1
            summary['by_status'][txn['status']] += 1
            summary['total_volume'] += txn['amount']
            summary['by_type_volume'][txn['transaction_type']] += txn['amount']
        
        return dict(summary)
    
    def top_accounts(self, top_n=10):
        """Find accounts with highest transaction volume"""
        account_volumes = defaultdict(float)
        
        for txn in self.transactions:
            if txn['status'] == 'COMPLETED':
                account_volumes[txn['account_number']] += txn['amount']
        
        sorted_accounts = sorted(account_volumes.items(), key=lambda x: x[1], reverse=True)
        return sorted_accounts[:top_n]
    
    def hourly_distribution(self):
        """Analyze transaction distribution by hour"""
        hourly = defaultdict(int)
        
        for txn in self.transactions:
            hour = datetime.strptime(txn['timestamp'], '%Y-%m-%d %H:%M:%S').hour
            hourly[hour] += 1
        
        return dict(sorted(hourly.items()))
    
    def location_analysis(self):
        """Analyze transactions by location"""
        location_stats = defaultdict(lambda: {'count': 0, 'volume': 0})
        
        for txn in self.transactions:
            loc = txn['location']
            location_stats[loc]['count'] += 1
            location_stats[loc]['volume'] += txn['amount']
        
        return dict(location_stats)
    
    def generate_report(self, output_file):
        """Generate comprehensive analytics report"""
        report = {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'daily_summary': self.daily_summary(),
            'top_accounts': self.top_accounts(),
            'hourly_distribution': self.hourly_distribution(),
            'location_analysis': self.location_analysis()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

if __name__ == '__main__':
    analytics = TransactionAnalytics()
    
    print("Loading transactions...")
    analytics.load_transactions('../data/sample_transactions.json')
    
    print("\nGenerating analytics report...")
    report = analytics.generate_report('../data/analytics_report.json')
    
    print(f"\n{'='*60}")
    print("DAILY TRANSACTION ANALYTICS")
    print(f"{'='*60}")
    
    summary = report['daily_summary']
    print(f"\nTotal Transactions: {summary['total_transactions']:,}")
    print(f"Total Volume: ${summary['total_volume']:,.2f}")
    
    print(f"\nTransactions by Type:")
    for txn_type, count in summary['by_type'].items():
        volume = summary['by_type_volume'][txn_type]
        print(f"  {txn_type}: {count:,} transactions (${volume:,.2f})")
    
    print(f"\nTransactions by Status:")
    for status, count in summary['by_status'].items():
        percentage = (count / summary['total_transactions']) * 100
        print(f"  {status}: {count:,} ({percentage:.1f}%)")
    
    print(f"\nTop 5 Accounts by Volume:")
    for i, (account, volume) in enumerate(report['top_accounts'][:5], 1):
        print(f"  {i}. {account}: ${volume:,.2f}")
    
    print(f"\nPeak Hours:")
    hourly = report['hourly_distribution']
    peak_hour = max(hourly.items(), key=lambda x: x[1])
    print(f"  Busiest hour: {peak_hour[0]}:00 with {peak_hour[1]} transactions")
    
    print(f"\nReport saved to: ../data/analytics_report.json")
