#!/usr/bin/env python3
"""
Fraud Detector with Kafka Integration
Consumes transactions from Kafka, detects fraud, produces alerts

MODES:
- File mode: Reads from file (original behavior)
- Kafka mode: Consumes from Kafka topic, produces alerts to Kafka
"""

import json
import time
from datetime import datetime
from collections import defaultdict, deque
from fraud_detector import FraudDetector
from config import KAFKA_CONFIG, APP_CONFIG, ENABLE_KAFKA

# Kafka imports (optional)
if ENABLE_KAFKA:
    try:
        from kafka import KafkaConsumer, KafkaProducer
        from kafka.errors import KafkaError
        KAFKA_AVAILABLE = True
    except ImportError:
        print("⚠️  kafka-python not installed. Run: pip install kafka-python")
        KAFKA_AVAILABLE = False
else:
    KAFKA_AVAILABLE = False


class FraudDetectorKafka(FraudDetector):
    """
    Enhanced fraud detector with Kafka support
    
    Inherits from original FraudDetector
    Adds Kafka consumer/producer capability
    """
    
    def __init__(self, use_kafka=False):
        """
        Initialize fraud detector
        
        Args:
            use_kafka: If True, use Kafka; if False, use files
        """
        super().__init__()
        self.use_kafka = use_kafka and KAFKA_AVAILABLE
        self.consumer = None
        self.producer = None
        self.running = False
        self.stats = {
            'consumed': 0,
            'processed': 0,
            'alerts_produced': 0,
            'errors': 0,
        }
        
        # Initialize Kafka if enabled
        if self.use_kafka:
            self._init_kafka()
    
    def _init_kafka(self):
        """Initialize Kafka consumer and producer"""
        try:
            # Consumer: Read transactions
            self.consumer = KafkaConsumer(
                KAFKA_CONFIG['topics']['transactions'],
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                **KAFKA_CONFIG['consumer']
            )
            
            # Producer: Send fraud alerts
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                **KAFKA_CONFIG['producer']
            )
            
            print("✅ Connected to Kafka")
            print(f"   Consuming from: {KAFKA_CONFIG['topics']['transactions']}")
            print(f"   Producing to: {KAFKA_CONFIG['topics']['fraud_alerts']}")
            
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {e}")
            print("   Falling back to file mode")
            self.use_kafka = False
            self.consumer = None
            self.producer = None
    
    def send_alert_to_kafka(self, alert):
        """
        Send fraud alert to Kafka topic
        
        Args:
            alert: Fraud alert dictionary
            
        Returns:
            bool: True if sent successfully
        """
        if not self.use_kafka or not self.producer:
            return False
        
        try:
            self.producer.send(
                KAFKA_CONFIG['topics']['fraud_alerts'],
                value=alert
            )
            self.stats['alerts_produced'] += 1
            return True
        except Exception as e:
            print(f"❌ Failed to send alert: {e}")
            self.stats['errors'] += 1
            return False
    
    def process_stream(self, max_messages=None, show_progress=True):
        """
        Process streaming transactions from Kafka
        
        Args:
            max_messages: Maximum messages to process (None = infinite)
            show_progress: Show progress messages
            
        Returns:
            list: All alerts detected
        """
        if not self.use_kafka or not self.consumer:
            print("❌ Kafka not available. Use file mode instead.")
            return []
        
        if show_progress:
            print("\n🔍 Starting fraud detection stream...")
            print(f"   Max messages: {max_messages if max_messages else 'unlimited'}")
            print(f"   Press Ctrl+C to stop")
            print()
        
        self.running = True
        all_alerts = []
        message_count = 0
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                
                # Extract transaction
                transaction = message.value
                self.stats['consumed'] += 1
                
                # Process for fraud
                alerts = self.process_transaction(transaction)
                self.stats['processed'] += 1
                
                # Send alerts to Kafka
                for alert in alerts:
                    self.send_alert_to_kafka(alert)
                    all_alerts.append(alert)
                
                message_count += 1
                
                # Show progress
                if show_progress and message_count % 100 == 0:
                    print(f"   Processed {message_count} transactions, "
                          f"{len(all_alerts)} alerts...")
                
                # Check if reached max
                if max_messages and message_count >= max_messages:
                    break
            
            # Flush producer
            if self.producer:
                self.producer.flush()
            
            if show_progress:
                print(f"\n✅ Fraud detection complete!")
                print(f"   Processed: {message_count} transactions")
                print(f"   Alerts: {len(all_alerts)}")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Stopped by user")
            self.running = False
        
        return all_alerts
    
    def get_stats(self):
        """Get processing statistics"""
        return {
            'consumed_from_kafka': self.stats['consumed'],
            'processed': self.stats['processed'],
            'alerts_produced': self.stats['alerts_produced'],
            'errors': self.stats['errors'],
            'mode': 'kafka' if self.use_kafka else 'file',
        }
    
    def close(self):
        """Close Kafka connections"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.close()
        print("✅ Kafka connections closed")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fraud Detection (File or Kafka mode)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # File mode (original behavior):
  python fraud_detector_kafka.py --file ../data/transactions.json
  
  # Kafka streaming mode (process 1000 messages):
  python fraud_detector_kafka.py --kafka --max 1000
  
  # Kafka streaming mode (continuous):
  python fraud_detector_kafka.py --kafka
        """
    )
    
    # Mode selection
    parser.add_argument('--kafka', action='store_true',
                       help='Consume from Kafka (requires Kafka running)')
    parser.add_argument('--file', type=str,
                       help='Process transactions from file')
    
    # Processing options
    parser.add_argument('--max', type=int, default=None,
                       help='Maximum messages to process (Kafka mode only)')
    
    args = parser.parse_args()
    
    # Create detector
    detector = FraudDetectorKafka(use_kafka=args.kafka)
    
    try:
        if args.kafka:
            # Kafka streaming mode
            print("=" * 70)
            print("KAFKA MODE - Real-Time Fraud Detection")
            print("=" * 70)
            
            alerts = detector.process_stream(
                max_messages=args.max,
                show_progress=True
            )
            
        elif args.file:
            # File mode (original)
            print("=" * 70)
            print("FILE MODE - Batch Fraud Detection")
            print("=" * 70)
            
            print(f"\nLoading transactions from {args.file}...")
            transactions = []
            with open(args.file, 'r') as f:
                for line in f:
                    transactions.append(json.loads(line))
            
            print(f"Processing {len(transactions)} transactions...")
            alerts = []
            for txn in transactions:
                txn_alerts = detector.process_transaction(txn)
                alerts.extend(txn_alerts)
            
            # Save alerts to file
            alert_file = APP_CONFIG['fraud_alerts_file']
            with open(alert_file, 'w') as f:
                json.dump(alerts, f, indent=2)
            print(f"✅ Saved {len(alerts)} alerts to {alert_file}")
        
        else:
            print("Error: Specify --kafka or --file mode")
            parser.print_help()
            exit(1)
        
        # Show statistics
        print("\n" + "=" * 70)
        print("STATISTICS")
        print("=" * 70)
        stats = detector.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Show fraud summary
        print("\n" + "=" * 70)
        print("FRAUD SUMMARY")
        print("=" * 70)
        summary = detector.get_fraud_summary()
        print(json.dumps(summary, indent=2))
        
        # Show sample alerts
        if alerts:
            print("\n" + "=" * 70)
            print("SAMPLE ALERTS")
            print("=" * 70)
            for alert in alerts[:5]:
                print(json.dumps(alert, indent=2))
                print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        detector.close()
