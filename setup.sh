#!/bin/bash

echo "🚀 Supabase CLI MCP Setup"
echo ""

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check for .env
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your Supabase credentials"
    exit 1
fi

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t supabase-cli-mcp .

# Stop existing container
docker rm -f supabase-cli 2>/dev/null || true

# Start container
echo "🚀 Starting MCP server..."
docker run -d \
  -p 5001:5001 \
  --env-file .env \
  -v "$(pwd)/functions":/app/functions \
  --name supabase-cli \
  supabase-cli-mcp

echo ""
echo "✅ Setup complete!"
echo ""
echo "To register with Claude Code:"
echo "claude mcp add supabase-local python3 $(pwd)/mcp-server.py"
