#!/bin/bash

# Project Helix Startup Script
# This script starts the Flask application with all new features

echo "🚀 Starting Project Helix..."
echo ""

# Navigate to Project directory
cd "$(dirname "$0")/Project" || exit

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your credentials."
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 No virtual environment found. Creating one..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check for required dependencies
echo ""
echo "🔍 Checking dependencies..."
python3 -c "import flask; print('✅ Flask installed')" 2>/dev/null || echo "❌ Flask not installed"
python3 -c "import flask_cors; print('✅ Flask-CORS installed')" 2>/dev/null || echo "❌ Flask-CORS not installed"
python3 -c "import dotenv; print('✅ python-dotenv installed')" 2>/dev/null || echo "❌ python-dotenv not installed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Project Helix is starting!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 New Features Available:"
echo "   • 📅 Export events to iCal/CSV"
echo "   • 📄 Pagination (30 events at a time)"
echo "   • 🌙 Dark mode toggle"
echo "   • 🔔 Enhanced toast notifications"
echo "   • 🔒 Secure API credentials"
echo ""
echo "🌐 Opening in browser: http://localhost:5001"
echo ""
echo "💡 Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Open browser (macOS)
sleep 2 && open http://localhost:5001 &

# Start Flask app
python3 app.py
