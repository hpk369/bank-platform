#!/usr/bin/env python3
"""
Configuration for Kafka and Spark Integration
Banking Transaction Processing Platform
"""

# ============================================================================
# KAFKA CONFIGURATION
# ============================================================================

KAFKA_CONFIG = {
    # Broker connection
    'bootstrap_servers': ['localhost:9092'],
    
    # Topic names
    'topics': {
        'transactions': 'banking-transactions',      # Raw transactions
        'fraud_alerts': 'fraud-alerts',              # Fraud detection results
        'processed': 'processed-transactions',       # Processed transactions
        'analytics': 'analytics-results',            # Analytics results
    },
    
    # Producer settings (for transaction generator)
    'producer': {
        'acks': 'all',  # Wait for all replicas to acknowledge (most reliable)
        'retries': 3,   # Retry 3 times on failure
        'max_in_flight_requests_per_connection': 1,  # Maintain order
        'compression_type': 'gzip',  # Compress data
        'linger_ms': 10,  # Wait 10ms to batch messages
    },
    
    # Consumer settings (for fraud detector, analytics)
    'consumer': {
        'group_id': 'banking-platform-consumers',
        'auto_offset_reset': 'earliest',  # Start from beginning if no offset
        'enable_auto_commit': True,
        'auto_commit_interval_ms': 1000,
        'max_poll_records': 500,  # Process 500 records at a time
    }
}

# ============================================================================
# SPARK CONFIGURATION
# ============================================================================

SPARK_CONFIG = {
    # Application settings
    'app_name': 'BankingPlatform',
    
    # Master URL
    # Development: Use local mode with all cores
    'master': 'local[*]',
    # Production: Use YARN cluster
    # 'master': 'yarn',
    
    # Memory settings
    'executor_memory': '2g',
    'driver_memory': '2g',
    'executor_cores': 2,
    
    # Streaming settings
    'streaming': {
        'batch_interval': 5,  # Process every 5 seconds
        'checkpoint_dir': '/tmp/spark-checkpoints',
    },
    
    # Kafka integration for Spark Streaming
    'kafka_integration': {
        'subscribe': 'banking-transactions',  # Topic to subscribe
        'startingOffsets': 'earliest',  # Start from beginning
        'failOnDataLoss': False,  # Continue even if data loss
    }
}

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================

APP_CONFIG = {
    # Batch processing
    'batch_size': 1000,  # Number of transactions per batch
    
    # Streaming intervals
    'transaction_stream_interval': 0.1,  # Generate transaction every 0.1s
    'spark_batch_interval': 5,  # Spark processes every 5 seconds
    
    # Fraud detection thresholds
    'fraud_thresholds': {
        'high_amount': 5000,
        'velocity_count': 5,
        'velocity_window': 300,  # 5 minutes in seconds
        'location_count': 3,
    },
    
    # File paths (fallback if Kafka unavailable)
    'data_dir': '../data',
    'transactions_file': '../data/transactions.json',
    'fraud_alerts_file': '../data/fraud_alerts.json',
    'analytics_file': '../data/analytics_report.json',
}

# ============================================================================
# MODES
# ============================================================================

# Set mode: 'file', 'kafka', 'spark_streaming', 'spark_batch'
DEFAULT_MODE = 'file'  # Start with file mode (existing functionality)

# Feature flags
ENABLE_KAFKA = False  # Set to True when Kafka is running
ENABLE_SPARK = False  # Set to True when Spark is available
