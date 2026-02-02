#!/usr/bin/env python3
"""
Fraud Detector with Spark Streaming
Uses Spark Streaming to process transactions from Kafka in real-time
Distributed across cluster for scalability

This demonstrates the FULL production architecture:
Kafka (streaming) → Spark Streaming (processing) → Kafka (alerts)
"""

import json
from config import KAFKA_CONFIG, SPARK_CONFIG, APP_CONFIG, ENABLE_SPARK

# Spark imports (optional)
if ENABLE_SPARK:
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import from_json, col, window, count
        from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
        SPARK_AVAILABLE = True
    except ImportError:
        print("⚠️  pyspark not installed. Run: pip install pyspark")
        SPARK_AVAILABLE = False
else:
    SPARK_AVAILABLE = False


class FraudDetectorSpark:
    """
    Fraud detection using Spark Streaming
    
    This is the PRODUCTION version that:
    - Reads from Kafka using Spark Streaming
    - Processes in distributed fashion across cluster
    - Writes alerts back to Kafka
    - Scales to millions of transactions
    """
    
    def __init__(self):
        """Initialize Spark Streaming application"""
        self.spark = None
        self.streaming_query = None
        
        if not SPARK_AVAILABLE:
            print("❌ Spark not available")
            return
        
        self._init_spark()
    
    def _init_spark(self):
        """Initialize Spark Session"""
        try:
            self.spark = SparkSession.builder \
                .appName(SPARK_CONFIG['app_name']) \
                .master(SPARK_CONFIG['master']) \
                .config("spark.executor.memory", SPARK_CONFIG['executor_memory']) \
                .config("spark.driver.memory", SPARK_CONFIG['driver_memory']) \
                .getOrCreate()
            
            # Set log level to reduce output
            self.spark.sparkContext.setLogLevel("WARN")
            
            print("✅ Spark Session initialized")
            print(f"   Master: {SPARK_CONFIG['master']}")
            print(f"   Executor Memory: {SPARK_CONFIG['executor_memory']}")
            
        except Exception as e:
            print(f"❌ Failed to initialize Spark: {e}")
            self.spark = None
    
    def define_transaction_schema(self):
        """Define schema for transaction data"""
        return StructType([
            StructField("transaction_id", StringType(), True),
            StructField("account_number", StringType(), True),
            StructField("transaction_type", StringType(), True),
            StructField("amount", DoubleType(), True),
            StructField("timestamp", StringType(), True),
            StructField("location", StringType(), True),
            StructField("merchant", StringType(), True),
            StructField("status", StringType(), True),
        ])
    
    def start_streaming(self, output_mode='console'):
        """
        Start Spark Streaming fraud detection
        
        Args:
            output_mode: 'console', 'kafka', or 'both'
        """
        if not self.spark:
            print("❌ Spark not initialized")
            return
        
        print("\n🚀 Starting Spark Streaming fraud detection...")
        print(f"   Reading from Kafka: {KAFKA_CONFIG['topics']['transactions']}")
        print(f"   Output mode: {output_mode}")
        print()
        
        try:
            # Read from Kafka
            df = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", 
                       ','.join(KAFKA_CONFIG['bootstrap_servers'])) \
                .option("subscribe", KAFKA_CONFIG['topics']['transactions']) \
                .option("startingOffsets", "earliest") \
                .load()
            
            # Parse JSON from Kafka value
            schema = self.define_transaction_schema()
            transactions = df.selectExpr("CAST(value AS STRING)") \
                .select(from_json(col("value"), schema).alias("data")) \
                .select("data.*")
            
            # FRAUD RULE 1: High Amount Transactions (> $5000)
            high_amount_alerts = transactions \
                .filter(col("amount") > APP_CONFIG['fraud_thresholds']['high_amount']) \
                .select(
                    col("transaction_id"),
                    col("account_number"),
                    col("amount"),
                    col("timestamp")
                ) \
                .withColumn("alert_type", col("transaction_id").cast("string") * 0 + "HIGH_AMOUNT") \
                .withColumn("severity", col("transaction_id").cast("string") * 0 + "HIGH")
            
            # FRAUD RULE 2: Velocity Check (5+ transactions in 5 minutes)
            # Group by account and time window
            velocity_alerts = transactions \
                .withWatermark("timestamp", "10 minutes") \
                .groupBy(
                    col("account_number"),
                    window(col("timestamp"), "5 minutes")
                ) \
                .agg(count("*").alias("txn_count")) \
                .filter(col("txn_count") >= APP_CONFIG['fraud_thresholds']['velocity_count'])
            
            # Output to console for monitoring
            if output_mode in ['console', 'both']:
                # High amount alerts to console
                query1 = high_amount_alerts \
                    .writeStream \
                    .outputMode("append") \
                    .format("console") \
                    .option("truncate", False) \
                    .start()
                
                # Velocity alerts to console
                query2 = velocity_alerts \
                    .writeStream \
                    .outputMode("update") \
                    .format("console") \
                    .option("truncate", False) \
                    .start()
                
                print("✅ Streaming to console...")
                print("   Press Ctrl+C to stop")
                print()
                
                # Wait for termination
                query1.awaitTermination()
                query2.awaitTermination()
            
            # Output to Kafka (production mode)
            if output_mode in ['kafka', 'both']:
                # Convert alerts to JSON and write to Kafka
                kafka_query = high_amount_alerts \
                    .selectExpr("to_json(struct(*)) AS value") \
                    .writeStream \
                    .format("kafka") \
                    .option("kafka.bootstrap.servers", 
                           ','.join(KAFKA_CONFIG['bootstrap_servers'])) \
                    .option("topic", KAFKA_CONFIG['topics']['fraud_alerts']) \
                    .option("checkpointLocation", "/tmp/kafka-checkpoint") \
                    .start()
                
                print("✅ Streaming to Kafka...")
                print(f"   Alerts topic: {KAFKA_CONFIG['topics']['fraud_alerts']}")
                print("   Press Ctrl+C to stop")
                print()
                
                kafka_query.awaitTermination()
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Stopped by user")
            self.stop()
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            self.stop()
    
    def batch_analysis(self, input_file):
        """
        Run batch fraud analysis on file (for testing/development)
        
        Args:
            input_file: Path to JSON file with transactions
        """
        if not self.spark:
            print("❌ Spark not initialized")
            return
        
        print(f"\n📊 Running batch fraud analysis...")
        print(f"   Input: {input_file}")
        print()
        
        try:
            # Read JSON file
            df = self.spark.read.json(input_file)
            
            # Show sample
            print("Sample transactions:")
            df.show(5, truncate=False)
            
            # Fraud detection: High amounts
            high_amount = df.filter(col("amount") > 5000)
            print(f"\n🚨 High amount transactions (> $5000):")
            high_amount.select("transaction_id", "account_number", "amount").show()
            
            # Fraud detection: Group by account to find velocity
            print(f"\n🚨 Transaction velocity by account:")
            df.groupBy("account_number") \
                .count() \
                .filter(col("count") > 10) \
                .orderBy(col("count").desc()) \
                .show()
            
            # Summary statistics
            print(f"\n📈 Summary:")
            df.groupBy("transaction_type") \
                .agg(
                    count("*").alias("count"),
                    sum("amount").alias("total_amount")
                ) \
                .show()
        
        except Exception as e:
            print(f"❌ Batch analysis error: {e}")
    
    def stop(self):
        """Stop Spark session"""
        if self.spark:
            self.spark.stop()
            print("✅ Spark session stopped")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fraud Detection with Spark Streaming',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Spark Streaming from Kafka (console output):
  python fraud_detector_spark.py --stream --console
  
  # Spark Streaming from Kafka (write alerts to Kafka):
  python fraud_detector_spark.py --stream --kafka
  
  # Spark Batch analysis on file:
  python fraud_detector_spark.py --batch ../data/transactions.json
  
PREREQUISITES:
  - Kafka must be running
  - Transactions must be flowing to Kafka
  - Run transaction_generator_kafka.py first
        """
    )
    
    # Mode selection
    parser.add_argument('--stream', action='store_true',
                       help='Start Spark Streaming mode')
    parser.add_argument('--batch', type=str,
                       help='Run batch analysis on file')
    
    # Output options (for streaming)
    parser.add_argument('--console', action='store_true',
                       help='Output to console (streaming only)')
    parser.add_argument('--kafka', action='store_true',
                       help='Output to Kafka (streaming only)')
    
    args = parser.parse_args()
    
    if not (args.stream or args.batch):
        print("Error: Specify --stream or --batch mode")
        parser.print_help()
        exit(1)
    
    # Create Spark fraud detector
    detector = FraudDetectorSpark()
    
    try:
        if args.stream:
            # Determine output mode
            if args.console and args.kafka:
                output_mode = 'both'
            elif args.kafka:
                output_mode = 'kafka'
            else:
                output_mode = 'console'
            
            print("=" * 70)
            print("SPARK STREAMING MODE - Real-Time Fraud Detection")
            print("=" * 70)
            
            detector.start_streaming(output_mode=output_mode)
        
        elif args.batch:
            print("=" * 70)
            print("SPARK BATCH MODE - Distributed Fraud Analysis")
            print("=" * 70)
            
            detector.batch_analysis(args.batch)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        detector.stop()
