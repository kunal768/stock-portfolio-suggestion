#!/bin/bash

# Stock Portfolio Suggestion Engine - Run Script
# This script sets up the virtual environment, installs dependencies, and starts both backend and frontend

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Stock Portfolio Suggestion Engine${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Step 1: Create virtual environment if it doesn't exist
echo -e "${YELLOW}Step 1: Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Step 2: Activate virtual environment
echo ""
echo -e "${YELLOW}Step 2: Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Step 3: Upgrade pip
echo ""
echo -e "${YELLOW}Step 3: Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"

# Step 4: Install backend requirements
echo ""
echo -e "${YELLOW}Step 4: Installing backend dependencies...${NC}"
pip install -r stock_portfolio_api/requirements.txt --quiet
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Step 5: Install frontend requirements
echo ""
echo -e "${YELLOW}Step 5: Installing frontend dependencies...${NC}"
pip install -r ui/requirements.txt --quiet
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

# Step 6: Start backend and frontend
echo ""
echo -e "${YELLOW}Step 6: Starting services...${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✓ Services stopped${NC}"
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

# Start backend in background
echo -e "${BLUE}Starting FastAPI backend on http://localhost:8000${NC}"
uvicorn stock_portfolio_api.main:app --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start frontend in background
echo -e "${BLUE}Starting Streamlit frontend on http://localhost:8501${NC}"
streamlit run ui/app.py &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}API Docs:${NC}    http://localhost:8000/docs"
echo -e "${BLUE}Frontend UI:${NC} http://localhost:8501"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

