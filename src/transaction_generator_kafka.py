#!/usr/bin/env python3
"""
Transaction Generator with Kafka Integration
Extends the original generator to support Kafka streaming

MODES:
- File mode: Same as original (backward compatible)
- Kafka mode: Streams transactions to Kafka topic
"""

import json
import random
import time
from datetime import datetime, timedelta
from transaction_generator import TransactionGenerator
from config import KAFKA_CONFIG, APP_CONFIG, ENABLE_KAFKA

# Kafka imports (optional - only if Kafka is enabled)
if ENABLE_KAFKA:
    try:
        from kafka import KafkaProducer
        from kafka.errors import KafkaError
        KAFKA_AVAILABLE = True
    except ImportError:
        print("⚠️  kafka-python not installed. Run: pip install kafka-python")
        KAFKA_AVAILABLE = False
else:
    KAFKA_AVAILABLE = False


class TransactionGeneratorKafka(TransactionGenerator):
    """
    Enhanced transaction generator with Kafka support
    
    Inherits from original TransactionGenerator
    Adds Kafka streaming capability
    """
    
    def __init__(self, num_accounts=500, use_kafka=False):
        """
        Initialize generator
        
        Args:
            num_accounts: Number of accounts to generate transactions for
            use_kafka: If True, send transactions to Kafka; if False, use files
        """
        super().__init__(num_accounts)
        self.use_kafka = use_kafka and KAFKA_AVAILABLE
        self.producer = None
        self.stats = {
            'sent_to_kafka': 0,
            'failed_to_kafka': 0,
            'saved_to_file': 0,
        }
        
        # Initialize Kafka producer if enabled
        if self.use_kafka:
            self._init_kafka_producer()
    
    def _init_kafka_producer(self):
        """Initialize Kafka producer connection"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                **KAFKA_CONFIG['producer']
            )
            print("✅ Connected to Kafka broker")
            print(f"   Bootstrap servers: {KAFKA_CONFIG['bootstrap_servers']}")
            print(f"   Topic: {KAFKA_CONFIG['topics']['transactions']}")
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {e}")
            print("   Falling back to file mode")
            self.use_kafka = False
            self.producer = None
    
    def send_to_kafka(self, transaction):
        """
        Send a single transaction to Kafka
        
        Args:
            transaction: Transaction dictionary
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.use_kafka or not self.producer:
            return False
        
        try:
            # Send to Kafka topic
            future = self.producer.send(
                KAFKA_CONFIG['topics']['transactions'],
                value=transaction
            )
            
            # Optional: Wait for confirmation (more reliable but slower)
            # record_metadata = future.get(timeout=10)
            
            self.stats['sent_to_kafka'] += 1
            return True
            
        except Exception as e:
            print(f"❌ Failed to send transaction {transaction['transaction_id']}: {e}")
            self.stats['failed_to_kafka'] += 1
            return False
    
    def generate_stream(self, count=100, interval=0.1, show_progress=True):
        """
        Generate streaming transactions (simulates real-time flow)
        
        Args:
            count: Number of transactions to generate
            interval: Time between transactions (seconds)
            show_progress: Show progress messages
            
        Returns:
            list: Generated transactions
        """
        if show_progress:
            mode = "Kafka" if self.use_kafka else "File"
            print(f"\n🚀 Starting transaction stream...")
            print(f"   Mode: {mode}")
            print(f"   Count: {count} transactions")
            print(f"   Interval: {interval}s between transactions")
            print()
        
        transactions = []
        
        for i in range(count):
            # Generate transaction
            txn = self.generate_transaction()
            transactions.append(txn)
            
            # Send to Kafka or keep in memory
            if self.use_kafka:
                self.send_to_kafka(txn)
            
            # Show progress
            if show_progress and (i + 1) % 100 == 0:
                print(f"   Generated {i + 1}/{count} transactions...")
            
            # Simulate real-time interval
            time.sleep(interval)
        
        # Flush Kafka producer to ensure all messages sent
        if self.use_kafka and self.producer:
            self.producer.flush()
        
        # Show final stats
        if show_progress:
            print(f"\n✅ Stream complete!")
            if self.use_kafka:
                print(f"   Sent to Kafka: {self.stats['sent_to_kafka']}")
                print(f"   Failed: {self.stats['failed_to_kafka']}")
            else:
                print(f"   Generated: {len(transactions)} (in memory)")
        
        # Fallback: Save to file if not using Kafka
        if not self.use_kafka:
            filename = APP_CONFIG['transactions_file']
            self.save_to_file(transactions, filename)
            self.stats['saved_to_file'] = len(transactions)
        
        return transactions
    
    def get_stats(self):
        """Get statistics about generated transactions"""
        return {
            'total_generated': self.transaction_counter,
            'sent_to_kafka': self.stats['sent_to_kafka'],
            'failed_to_kafka': self.stats['failed_to_kafka'],
            'saved_to_file': self.stats['saved_to_file'],
            'mode': 'kafka' if self.use_kafka else 'file',
        }
    
    def close(self):
        """Close Kafka producer connection"""
        if self.producer:
            self.producer.close()
            print("✅ Kafka producer closed")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate banking transactions (File or Kafka mode)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # File mode (original behavior):
  python transaction_generator_kafka.py --count 1000
  
  # Kafka streaming mode:
  python transaction_generator_kafka.py --count 1000 --kafka --stream
  
  # Fast streaming (10 txns/sec):
  python transaction_generator_kafka.py --count 1000 --kafka --stream --interval 0.1
  
  # Slow streaming (1 txn/sec) for testing:
  python transaction_generator_kafka.py --count 100 --kafka --stream --interval 1.0
        """
    )
    
    # Basic options
    parser.add_argument('--count', type=int, default=1000,
                       help='Number of transactions to generate (default: 1000)')
    parser.add_argument('--accounts', type=int, default=500,
                       help='Number of accounts (default: 500)')
    
    # Mode options
    parser.add_argument('--kafka', action='store_true',
                       help='Send transactions to Kafka (requires Kafka running)')
    parser.add_argument('--stream', action='store_true',
                       help='Stream transactions in real-time (slower)')
    parser.add_argument('--interval', type=float, default=0.1,
                       help='Interval between transactions in seconds (default: 0.1)')
    
    args = parser.parse_args()
    
    # Create generator
    generator = TransactionGeneratorKafka(
        num_accounts=args.accounts,
        use_kafka=args.kafka
    )
    
    try:
        if args.stream:
            # Streaming mode - simulates real-time transactions
            print("=" * 70)
            print("STREAMING MODE - Simulating Real-Time Transactions")
            print("=" * 70)
            transactions = generator.generate_stream(
                count=args.count,
                interval=args.interval
            )
        else:
            # Batch mode - generate all at once
            print("=" * 70)
            print("BATCH MODE - Generating All Transactions at Once")
            print("=" * 70)
            print(f"\nGenerating {args.count} transactions...")
            transactions = generator.generate_batch(args.count)
            
            if args.kafka:
                print(f"Sending to Kafka...")
                for txn in transactions:
                    generator.send_to_kafka(txn)
                if generator.producer:
                    generator.producer.flush()
                print(f"✅ Sent {len(transactions)} transactions to Kafka")
            else:
                filename = APP_CONFIG['transactions_file']
                generator.save_to_file(transactions, filename)
        
        # Show statistics
        print("\n" + "=" * 70)
        print("STATISTICS")
        print("=" * 70)
        stats = generator.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Show sample transactions
        print("\n" + "=" * 70)
        print("SAMPLE TRANSACTIONS")
        print("=" * 70)
        for txn in transactions[:3]:
            print(json.dumps(txn, indent=2))
            print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        generator.close()
