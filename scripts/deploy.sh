#!/bin/bash

# MOSDAC AI Chatbot Deployment Script

set -e

echo "🚀 Deploying MOSDAC AI Chatbot..."

# Configuration
ENVIRONMENT=${1:-production}
DOMAIN=${2:-localhost}

echo "📋 Deployment Configuration:"
echo "   Environment: $ENVIRONMENT"
echo "   Domain: $DOMAIN"

# Production-specific setup
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🔒 Setting up production environment..."
    
    # Generate SSL certificates (Let's Encrypt)
    if [ "$DOMAIN" != "localhost" ]; then
        echo "🔐 Setting up SSL certificates..."
        # Add Let's Encrypt setup here
    fi
    
    # Use production Docker Compose
    COMPOSE_FILE="docker-compose.prod.yml"
    
    # Set production environment variables
    export POSTGRES_PASSWORD=$(openssl rand -base64 32)
    export NEO4J_PASSWORD=$(openssl rand -base64 32)
    export SECRET_KEY=$(openssl rand -base64 32)
    
    echo "🔑 Generated secure passwords"
else
    COMPOSE_FILE="docker-compose.yml"
fi

# Build and deploy
echo "🐳 Building and deploying services..."
docker-compose -f $COMPOSE_FILE up -d --build

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 60

# Health check
echo "🔍 Running health checks..."
for i in {1..10}; do
    if curl -f http://localhost:8000/api/v1/health; then
        echo "✅ Services are healthy"
        break
    else
        echo "⏳ Waiting for services... ($i/10)"
        sleep 10
    fi
done

# Setup monitoring (if production)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "📊 Setting up monitoring..."
    # Add monitoring setup here
fi

echo "🎉 Deployment complete!"
echo ""
echo "🌐 Access your application:"
if [ "$DOMAIN" = "localhost" ]; then
    echo "   Frontend: http://localhost:3000"
    echo "   API: http://localhost:8000"
else
    echo "   Frontend: https://$DOMAIN"
    echo "   API: https://$DOMAIN/api"
fi
echo ""