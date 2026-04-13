#!/bin/bash

# Local Development Quick Start Script
# Usage: ./dev-start.sh

set -e

echo "🚀 ShopERP Local Development Setup"
echo "=================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to load .env.local
load_env() {
    if [ -f "$1" ]; then
        export $(grep -v '^#' "$1" | grep -v '^$' | xargs)
    fi
}

# 1. Start Docker services
echo -e "${BLUE}1. Starting PostgreSQL & PgAdmin...${NC}"
docker compose -f docker-compose.dev.yml up -d
echo -e "${GREEN}✓ Docker services started${NC}"
echo "   PgAdmin: http://localhost:5050"
echo "   PostgreSQL: localhost:5432"

# Wait for PostgreSQL to be ready
echo "   Waiting for PostgreSQL to be ready..."
sleep 5

# 2. Backend setup
echo -e "${BLUE}2. Setting up Backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "   Installing dependencies..."
pip install -q -r requirements.txt

echo "   Loading environment variables..."
load_env .env.local

echo "   Generating Prisma client..."
prisma generate

echo "   Running migrations..."
prisma migrate dev --skip-generate

echo -e "${GREEN}✓ Backend ready${NC}"
cd ..

# 3. Frontend setup
echo -e "${BLUE}3. Setting up Frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install -q
fi

echo -e "${GREEN}✓ Frontend ready${NC}"
cd ..

echo ""
echo -e "${GREEN}=================================="
echo "✓ Setup Complete!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Backend (in new terminal):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   export \$(grep -v '^#' .env.local | grep -v '^\$' | xargs)"
echo "   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Frontend (in new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Access:"
echo "   Frontend: http://localhost:5173"
echo "   Backend: http://localhost:8000"
echo "   PgAdmin: http://localhost:5050"
echo ""
echo "For more info, see LOCAL_DEV_SETUP.md"
