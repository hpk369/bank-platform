#!/bin/bash
# Quick system health check

echo "======================================"
echo "Banking Platform - Health Check"
echo "======================================"
echo ""

cd "$(dirname "$0")/../src" || exit

python3 monitor.py

echo ""
echo "Health check complete!"
