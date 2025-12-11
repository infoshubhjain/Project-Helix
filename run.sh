#!/bin/bash

# EventFlow - Quick Run Script
# This script starts the Flask development server

echo "Starting EventFlow..."
echo ""

# Check if port 5001 is in use
PORT_IN_USE=$(lsof -ti:5001)

if [ ! -z "$PORT_IN_USE" ]; then
  echo "⚠️  Port 5001 is already in use by process(es): $PORT_IN_USE"
  echo "🔧 Killing existing processes..."
  kill -9 $PORT_IN_USE 2>/dev/null
  sleep 1
  echo "✅ Port 5001 is now free"
  echo ""
fi

echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║  Starting Flask server on http://localhost:5001        ║"
echo "║                                                        ║"
echo "║  Press Ctrl+C to stop the server                      ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Open browser automatically after a short delay
(sleep 2 && open http://localhost:5001) &

cd Project
python3 app.py
