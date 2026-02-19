#!/bin/bash
set -e

echo "======================================"
echo "  TeamAI - Department Intelligence"
echo "  K2 Think x OpenClaw Hackathon"
echo "======================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
  echo "ERROR: Python 3 required. Install from https://python.org"
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python $PYTHON_VERSION found"

# Create virtualenv
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "Dependencies installed."

# Create data directories
mkdir -p data/chroma openclaw/workspace/meetings

# Check for .env
if [ ! -f ".env" ]; then
  cp .env.example .env 2>/dev/null || true
  echo "WARNING: .env file created. Add your K2_API_KEY."
fi

# Optional: Setup OpenClaw
echo ""
echo "======================================"
echo "  OPTIONAL: OpenClaw Setup"
echo "======================================"
echo ""
echo "OpenClaw provides the execution layer (tool invocation, task board sync)."
echo "The app works without it in fallback mode."
echo ""
echo "To enable OpenClaw:"
echo "  1. Install: npm install -g openclaw  (requires Node 22+)"
echo "  2. Setup:   openclaw onboard --install-daemon"
echo "  3. Config:  cp openclaw/openclaw.json ~/.openclaw/openclaw.json"
echo "  4. Start:   openclaw dashboard"
echo ""

echo "======================================"
echo "  Starting TeamAI Backend..."
echo "======================================"
echo ""
echo "Dashboard: http://localhost:8001"
echo "API Docs:  http://localhost:8001/docs"
echo ""

uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
