#!/usr/bin/env python3
"""
Banking Transaction Generator
Generates realistic banking transactions for testing
"""

import json
import random
from datetime import datetime, timedelta

class TransactionGenerator:
    """Generate realistic banking transactions"""
    
    TRANSACTION_TYPES = ['DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'PAYMENT']
    LOCATIONS = [
        'ATM-Downtown-01', 'ATM-Uptown-02', 'ATM-Westside-03',
        'Branch-Main-Street', 'Branch-5th-Avenue', 'Online-Portal',
        'Mobile-App', 'POS-Retail-Store', 'POS-Restaurant', 'POS-Gas-Station'
    ]
    MERCHANTS = [
        'Amazon', 'Walmart', 'Starbucks', 'Shell Gas', 'Best Buy',
        'Target', 'McDonalds', 'Apple Store', 'Whole Foods', None
    ]
    STATUSES = ['PENDING', 'COMPLETED', 'FAILED']
    
    def __init__(self, num_accounts=1000):
        self.num_accounts = num_accounts
        self.accounts = [f"ACC-{str(i).zfill(10)}" for i in range(1, num_accounts + 1)]
        self.transaction_counter = 0
    
    def generate_transaction(self):
        """Generate a single transaction"""
        self.transaction_counter += 1
        
        transaction_type = random.choice(self.TRANSACTION_TYPES)
        
        # Different amount ranges for different transaction types
        if transaction_type == 'DEPOSIT':
            amount = round(random.uniform(50, 5000), 2)
        elif transaction_type == 'WITHDRAWAL':
            amount = round(random.uniform(20, 1000), 2)
        elif transaction_type == 'TRANSFER':
            amount = round(random.uniform(10, 10000), 2)
        else:  # PAYMENT
            amount = round(random.uniform(5, 500), 2)
        
        # Timestamp within last 24 hours
        now = datetime.now()
        timestamp = now - timedelta(seconds=random.randint(0, 86400))
        
        transaction = {
            'transaction_id': f"TXN-{timestamp.strftime('%Y%m%d')}-{str(self.transaction_counter).zfill(8)}",
            'account_number': random.choice(self.accounts),
            'transaction_type': transaction_type,
            'amount': amount,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'location': random.choice(self.LOCATIONS),
            'merchant': random.choice(self.MERCHANTS) if transaction_type == 'PAYMENT' else None,
            'status': random.choices(self.STATUSES, weights=[10, 85, 5])[0]
        }
        
        return transaction
    
    def generate_batch(self, count=1000):
        """Generate a batch of transactions"""
        return [self.generate_transaction() for _ in range(count)]
    
    def save_to_file(self, transactions, filename):
        """Save transactions to JSON file"""
        with open(filename, 'w') as f:
            for txn in transactions:
                f.write(json.dumps(txn) + '\n')
        print(f"Saved {len(transactions)} transactions to {filename}")

if __name__ == '__main__':
    generator = TransactionGenerator(num_accounts=500)
    print("Generating 10,000 sample transactions...")
    transactions = generator.generate_batch(10000)
    generator.save_to_file(transactions, '../data/sample_transactions.json')
    
    print("\nSample transactions:")
    for txn in transactions[:5]:
        print(json.dumps(txn, indent=2))
