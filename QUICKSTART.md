# Quick Setup Guide - Banking Platform Mini

## 5-Minute Setup

### Step 1: Verify Python
```bash
python3 --version
# Should be 3.8 or higher
```

### Step 2: Install Dependencies
```bash
pip install psutil
# Or: pip3 install psutil
```

### Step 3: Navigate to Project
```bash
cd banking-platform-mini
```

### Step 4: Run the Platform
```bash
cd src
python3 main.py
```

## Expected Output

You should see:
1. ✅ System health check
2. ✅ 10,000 transactions generated
3. ✅ Fraud detection results (~1,200-1,500 alerts)
4. ✅ Analytics summary
5. ✅ Final report

Total runtime: ~3-5 seconds

## Verify Success

Check these files were created:
```bash
ls -lh data/
# Should show:
# - sample_transactions.json (~1-2 MB)
# - analytics_report.json
# - health_report.json
```

## Troubleshooting

**Problem: "No module named 'psutil'"**
Solution: `pip install psutil`

**Problem: "Permission denied"**
Solution: `chmod +x scripts/*.sh`

**Problem: "No such file or directory: data/"**
Solution: `mkdir -p data`

## Individual Components

Run each component separately:

```bash
# Generate transactions only
python3 transaction_generator.py

# Fraud detection only (requires data file)
python3 fraud_detector.py

# Analytics only (requires data file)
python3 analytics.py

# Health check only
python3 monitor.py
```

## What to Show Recruiters

1. Run: `python3 main.py`
2. Show the real-time output
3. Open: `../data/analytics_report.json`
4. Explain the architecture and your role

## Key Talking Points

- "I built this to demonstrate production Apps Support capabilities"
- "It processes 10,000 transactions in seconds with real-time fraud detection"
- "The system includes comprehensive monitoring and automated reporting"
- "This showcases my understanding of financial services applications"

Ready to add to your resume! 🚀
