#!/bin/bash

# MOSDAC AI Chatbot Test Script

set -e

echo "🧪 Running MOSDAC AI Chatbot Tests..."

# Backend tests
echo "🔧 Running backend tests..."
cd backend
python -m pytest tests/ -v --cov=app --cov-report=html
cd ..

# Frontend tests
echo "⚛️ Running frontend tests..."
npm test

# Integration tests
echo "🔗 Running integration tests..."
python -m pytest tests/integration/ -v

# API tests
echo "🌐 Running API tests..."
curl -X POST "http://localhost:8000/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "What is INSAT-3D?", "session_id": "test"}' \
     | jq .

# Load tests (optional)
echo "⚡ Would you like to run load tests? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "🚀 Running load tests..."
    # Add load testing here (e.g., with locust)
fi

echo "✅ All tests completed!"