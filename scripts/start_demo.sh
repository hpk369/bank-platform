#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Bank Platform — Live Spark Streaming Demo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Generate dataset if missing ────────────────────────────────────────
if [ ! -f "data/transactions_demo.csv.gz" ]; then
  echo ""
  echo "⚙  Dataset not found — generating now…"
  python3 scripts/generate_dataset.py
fi

# ── 2. Install Python deps if missing ─────────────────────────────────────
python3 -c "import fastapi" 2>/dev/null || {
  echo ""
  echo "📦  Installing Python dependencies…"
  pip install -r requirements-demo.txt -q
}

# ── 3. Launch API server ───────────────────────────────────────────────────
PORT="${PORT:-8000}"
echo ""
echo "🚀  Starting API server on http://localhost:$PORT"
echo "    Press Ctrl+C to stop."
echo ""
cd src/
python3 api_server.py --port "$PORT"
