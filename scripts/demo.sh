#!/bin/bash
#
# Banking Platform - Quick Demo Script
# Demonstrates all three modes: File, Kafka, Spark
#

echo "======================================================================"
echo "BANKING PLATFORM - KAFKA + SPARK DEMO"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check dependencies
check_dependency() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        return 1
    fi
}

echo "Checking dependencies..."
check_dependency python3
check_dependency kafka-topics

echo ""
echo "======================================================================"
echo "MODE 1: FILE-BASED (ORIGINAL)"
echo "======================================================================"
echo ""
echo "This mode uses files for data exchange (no Kafka/Spark needed)"
echo ""

read -p "Run File Mode demo? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Running original pipeline...${NC}"
    cd src/
    python3 main.py
    cd ..
    echo ""
    echo -e "${GREEN}✓ File mode complete!${NC}"
    echo "  Check data/ folder for outputs"
fi

echo ""
echo "======================================================================"
echo "MODE 2: KAFKA STREAMING"
echo "======================================================================"
echo ""
echo "This mode uses Kafka for real-time streaming"
echo ""
echo "Prerequisites:"
echo "  1. Kafka must be running: brew services start kafka"
echo "  2. Topics must be created (see KAFKA_SPARK_GUIDE.md)"
echo ""

read -p "Run Kafka Mode demo? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if Kafka is running
    if kafka-topics --list --bootstrap-server localhost:9092 &> /dev/null; then
        echo -e "${GREEN}✓ Kafka is running${NC}"
        
        # Create topics if they don't exist
        echo "Creating Kafka topics..."
        kafka-topics --create --if-not-exists \
            --topic banking-transactions \
            --bootstrap-server localhost:9092 \
            --partitions 3 --replication-factor 1 &> /dev/null
        
        kafka-topics --create --if-not-exists \
            --topic fraud-alerts \
            --bootstrap-server localhost:9092 \
            --partitions 3 --replication-factor 1 &> /dev/null
        
        echo -e "${GREEN}✓ Topics ready${NC}"
        echo ""
        
        echo -e "${YELLOW}Starting Kafka demo...${NC}"
        echo ""
        echo "This will:"
        echo "  1. Generate 100 transactions and send to Kafka"
        echo "  2. Consume from Kafka and detect fraud"
        echo ""
        
        cd src/
        
        # Generate transactions
        echo "Step 1: Generating transactions..."
        python3 transaction_generator_kafka.py --count 100 --kafka --stream --interval 0.05
        
        echo ""
        echo "Step 2: Detecting fraud..."
        python3 fraud_detector_kafka.py --kafka --max 100
        
        cd ..
        
        echo ""
        echo -e "${GREEN}✓ Kafka mode complete!${NC}"
        echo ""
        echo "View Kafka messages:"
        echo "  kafka-console-consumer --bootstrap-server localhost:9092 --topic fraud-alerts --from-beginning"
    else
        echo -e "${RED}✗ Kafka is not running${NC}"
        echo ""
        echo "Start Kafka with:"
        echo "  brew services start zookeeper"
        echo "  brew services start kafka"
    fi
fi

echo ""
echo "======================================================================"
echo "MODE 3: SPARK STREAMING"
echo "======================================================================"
echo ""
echo "This mode uses Spark Streaming for distributed processing"
echo ""

read -p "Run Spark Mode demo? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Running Spark batch analysis...${NC}"
    echo ""
    
    cd src/
    
    # First generate some data if it doesn't exist
    if [ ! -f "../data/sample_transactions.json" ]; then
        echo "Generating sample data..."
        python3 transaction_generator.py
    fi
    
    # Run Spark batch analysis
    python3 fraud_detector_spark.py --batch ../data/sample_transactions.json
    
    cd ..
    
    echo ""
    echo -e "${GREEN}✓ Spark batch analysis complete!${NC}"
    echo ""
    echo "For Spark Streaming, run:"
    echo "  Terminal 1: python3 transaction_generator_kafka.py --kafka --stream --count 1000"
    echo "  Terminal 2: python3 fraud_detector_spark.py --stream --console"
fi

echo ""
echo "======================================================================"
echo "DEMO COMPLETE"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Read KAFKA_SPARK_GUIDE.md for detailed instructions"
echo "  2. Try different modes and compare performance"
echo "  3. Modify fraud detection rules in config.py"
echo "  4. Add this to your resume/portfolio!"
echo ""
echo "Documentation:"
echo "  - KAFKA_SPARK_GUIDE.md - Complete setup guide"
echo "  - README.md - Project overview"
echo "  - src/config.py - Configuration settings"
echo ""
