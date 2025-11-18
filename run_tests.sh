#!/bin/bash

# Reader3 Test Runner Script
# Provides easy ways to run different test suites

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
check_venv() {
    if [ -z "$VIRTUAL_ENV" ] && [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Warning: No virtual environment found${NC}"
        echo "Creating virtual environment..."
        uv venv
        echo -e "${GREEN}Virtual environment created. Activating...${NC}"
        source .venv/bin/activate
        echo "Installing dependencies..."
        uv sync --extra dev
    elif [ -z "$VIRTUAL_ENV" ]; then
        echo "Activating virtual environment..."
        source .venv/bin/activate
    fi
}

# Display usage information
usage() {
    echo -e "${BLUE}Reader3 Test Runner${NC}"
    echo ""
    echo "Usage: ./run_tests.sh [command]"
    echo ""
    echo "Commands:"
    echo "  all           Run all tests (default)"
    echo "  unit          Run unit tests only"
    echo "  integration   Run integration tests only"
    echo "  fast          Run fast tests (skip slow tests)"
    echo "  coverage      Run tests with coverage report"
    echo "  watch         Run tests in watch mode (auto-rerun on changes)"
    echo "  docker        Test Docker build"
    echo "  clean         Clean test artifacts and cache"
    echo "  install       Install test dependencies"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh unit"
    echo "  ./run_tests.sh coverage"
    echo "  ./run_tests.sh fast"
}

# Install test dependencies
install_deps() {
    echo -e "${BLUE}Installing test dependencies...${NC}"
    check_venv
    uv sync --extra dev
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

# Run all tests
run_all() {
    echo -e "${BLUE}Running all tests...${NC}"
    check_venv
    pytest -v -m "not ai"
}

# Run unit tests
run_unit() {
    echo -e "${BLUE}Running unit tests...${NC}"
    check_venv
    pytest -v -m unit
}

# Run integration tests
run_integration() {
    echo -e "${BLUE}Running integration tests...${NC}"
    check_venv
    pytest -v -m integration
}

# Run fast tests
run_fast() {
    echo -e "${BLUE}Running fast tests (skipping slow tests)...${NC}"
    check_venv
    pytest -v -m "not slow and not ai"
}

# Run tests with coverage
run_coverage() {
    echo -e "${BLUE}Running tests with coverage...${NC}"
    check_venv
    pytest -v --cov=. --cov-report=html --cov-report=term-missing -m "not ai"
    echo ""
    echo -e "${GREEN}✓ Coverage report generated${NC}"
    echo -e "Open ${BLUE}htmlcov/index.html${NC} to view the report"
}

# Watch mode
run_watch() {
    echo -e "${BLUE}Running tests in watch mode...${NC}"
    check_venv

    # Check if pytest-watch is installed
    if ! python -c "import pytest_watch" 2>/dev/null; then
        echo "Installing pytest-watch..."
        uv add --dev pytest-watch
    fi

    ptw -- -v -m "not ai and not slow"
}

# Test Docker build
test_docker() {
    echo -e "${BLUE}Testing Docker build...${NC}"

    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}✗ Docker is not running${NC}"
        exit 1
    fi

    # Build image
    echo "Building Docker image..."
    docker build -t reader3:test .

    # Test if image runs
    echo "Testing Docker image..."
    docker run --rm reader3:test python -c "import server; print('OK')"

    echo -e "${GREEN}✓ Docker build successful${NC}"
}

# Clean test artifacts
clean() {
    echo -e "${BLUE}Cleaning test artifacts...${NC}"

    # Remove pytest cache
    rm -rf .pytest_cache
    rm -rf tests/__pycache__
    rm -rf __pycache__

    # Remove coverage files
    rm -rf htmlcov
    rm -f .coverage
    rm -f coverage.xml

    # Remove test databases
    rm -f test*.db

    # Remove Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    echo -e "${GREEN}✓ Cleaned test artifacts${NC}"
}

# Main script logic
case "${1:-all}" in
    all)
        run_all
        ;;
    unit)
        run_unit
        ;;
    integration)
        run_integration
        ;;
    fast)
        run_fast
        ;;
    coverage)
        run_coverage
        ;;
    watch)
        run_watch
        ;;
    docker)
        test_docker
        ;;
    clean)
        clean
        ;;
    install)
        install_deps
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        usage
        exit 1
        ;;
esac
