#!/bin/bash

# MOSDAC AI Chatbot Setup Script

set -e

echo "🚀 Setting up MOSDAC AI Chatbot..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/{raw,processed,pdfs,metadata,embeddings,knowledge_graph}
mkdir -p logs
mkdir -p nginx/ssl

# Copy environment file
if [ ! -f backend/.env ]; then
    echo "📝 Creating environment file..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env with your configuration"
fi

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
curl -f http://localhost:8000/api/v1/health || echo "⚠️  API service not ready yet"

# Initialize data (optional)
echo "📊 Would you like to run initial data scraping? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "🕷️ Starting initial data scraping..."
    curl -X POST "http://localhost:8000/api/v1/data/scrape" \
         -H "Content-Type: application/json" \
         -d '{"max_pages": 20, "max_depth": 2}'
    echo "✅ Scraping started in background"
fi

echo "🎉 Setup complete!"
echo ""
echo "🌐 Services available at:"
echo "   Frontend: http://localhost:3000"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Neo4j Browser: http://localhost:7474"
echo "   Flower (Celery): http://localhost:5555"
echo ""
echo "📚 Next steps:"
echo "   1. Edit backend/.env with your API keys"
echo "   2. Visit http://localhost:3000 to use the chatbot"
echo "   3. Check logs: docker-compose logs -f"
echo ""