#!/bin/bash

# EOL Scanner API Startup Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting EOL Scanner API...${NC}"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python -m venv .venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📥 Installing dependencies...${NC}"
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚙️  Creating .env file from template...${NC}"
    cp config.env.example .env
    echo -e "${RED}⚠️  Please edit .env file with your API_TOKEN and GITHUB_TOKEN${NC}"
    echo -e "${YELLOW}   Then run this script again.${NC}"
    exit 1
fi

# Load environment variables
echo -e "${YELLOW}🔐 Loading environment variables...${NC}"
export $(cat .env | grep -v '^#' | xargs)

# Check required environment variables
if [ -z "$API_TOKEN" ]; then
    echo -e "${RED}❌ API_TOKEN not set in .env file${NC}"
    exit 1
fi

# Start the API server
echo -e "${GREEN}🌐 Starting API server on http://localhost:8000${NC}"
echo -e "${YELLOW}📚 API Documentation: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}🔍 Health Check: http://localhost:8000/health${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start the server
python -m eolscan.api
