#!/bin/bash
# Run the complete Banking Platform pipeline

echo "======================================"
echo "Banking Platform - Pipeline Execution"
echo "======================================"
echo ""

cd "$(dirname "$0")/../src" || exit

python3 main.py

echo ""
echo "Pipeline execution complete!"
echo "Check the data/ directory for generated reports."
