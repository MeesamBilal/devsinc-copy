#!/bin/bash

# Voice Agent Startup Script

echo "🎙️  Voice Agent - Real-time AI Customer Support"
echo "================================================"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "🔧 Please edit .env file and add your API keys:"
    echo "   - DEEPGRAM_API_KEY=your_deepgram_api_key_here"
    echo "   - OPENAI_API_KEY=your_openai_api_key_here"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run tests first
echo ""
echo "🧪 Running system tests..."
python test_voice_agent.py

# Check test exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🚀 Starting Voice Agent..."
    echo "Press Ctrl+C to stop"
    echo ""
    python main.py
else
    echo ""
    echo "❌ Tests failed. Please fix the issues before running the voice agent."
    echo "Check your API keys and configuration."
    exit 1
fi