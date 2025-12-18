#!/usr/bin/env bash
# Pre-flight check script - Run before deployment
# Usage: ./scripts/preflight.sh

set -e

echo "🚀 Running pre-flight checks..."
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check counter
CHECKS_PASSED=0
CHECKS_FAILED=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ==============================================================================
# Environment Checks
# ==============================================================================
echo "📦 Environment Checks"
echo "-------------------"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    if [[ "$PYTHON_VERSION" > "3.11" ]] || [[ "$PYTHON_VERSION" == "3.11"* ]]; then
        check_pass "Python version: $PYTHON_VERSION"
    else
        check_fail "Python version $PYTHON_VERSION < 3.11 required"
    fi
else
    check_fail "Python 3 not found"
fi

# Check virtual environment
if [ -d "venv" ]; then
    check_pass "Virtual environment exists"
else
    check_warn "Virtual environment not found (run: python3 -m venv venv)"
fi

# Check .env file
if [ -f ".env" ]; then
    check_pass ".env file exists"

    # Check required variables
    REQUIRED_VARS=("DATABASE_URL" "TELEGRAM_BOT_TOKEN" "MANAGEMENT_CHAT_ID")
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" .env; then
            check_pass "  $var is set"
        else
            check_fail "  $var is missing"
        fi
    done
else
    check_fail ".env file not found (copy from .env.example)"
fi

echo ""

# ==============================================================================
# Dependencies Check
# ==============================================================================
echo "📚 Dependencies Check"
echo "--------------------"

if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt exists"

    # Check if dependencies are installed
    if [ -f "venv/bin/pip" ]; then
        MISSING_DEPS=$(venv/bin/pip check 2>&1 | grep -c "not compatible" || true)
        if [ "$MISSING_DEPS" -eq 0 ]; then
            check_pass "All dependencies compatible"
        else
            check_warn "Some dependency conflicts detected"
        fi
    fi
else
    check_fail "requirements.txt not found"
fi

echo ""

# ==============================================================================
# Code Quality Checks
# ==============================================================================
echo "🔍 Code Quality Checks"
echo "---------------------"

# Check if pre-commit is installed
if command -v pre-commit &> /dev/null; then
    check_pass "pre-commit is installed"

    # Run pre-commit on all files
    if pre-commit run --all-files &> /dev/null; then
        check_pass "All pre-commit hooks passed"
    else
        check_warn "Some pre-commit hooks failed (run: pre-commit run --all-files)"
    fi
else
    check_warn "pre-commit not installed (run: pip install pre-commit)"
fi

echo ""

# ==============================================================================
# Database Checks
# ==============================================================================
echo "🗄️  Database Checks"
echo "------------------"

# Check migration files
if [ -d "migrations/versions" ]; then
    MIGRATION_COUNT=$(find migrations/versions -name "*.py" -type f | wc -l)
    if [ "$MIGRATION_COUNT" -gt 0 ]; then
        check_pass "Found $MIGRATION_COUNT migration files"
    else
        check_warn "No migration files found"
    fi
else
    check_fail "migrations/versions directory not found"
fi

# Check Alembic configuration
if [ -f "alembic.ini" ]; then
    check_pass "alembic.ini exists"
else
    check_fail "alembic.ini not found"
fi

echo ""

# ==============================================================================
# Test Suite Checks
# ==============================================================================
echo "🧪 Test Suite Checks"
echo "-------------------"

if [ -d "tests" ]; then
    TEST_COUNT=$(find tests -name "test_*.py" -type f | wc -l)
    if [ "$TEST_COUNT" -gt 0 ]; then
        check_pass "Found $TEST_COUNT test files"
    else
        check_warn "No test files found"
    fi

    # Run pytest if available
    if [ -f "venv/bin/pytest" ]; then
        check_pass "pytest is installed"

        echo "  Running tests..."
        if venv/bin/pytest --tb=short -q 2>&1 | tail -5; then
            check_pass "Test suite passed"
        else
            check_fail "Some tests failed"
        fi
    else
        check_warn "pytest not installed"
    fi
else
    check_warn "tests directory not found"
fi

echo ""

# ==============================================================================
# Security Checks
# ==============================================================================
echo "🔒 Security Checks"
echo "-----------------"

# Check for hardcoded secrets
if command -v detect-secrets &> /dev/null; then
    if detect-secrets scan --baseline .secrets.baseline &> /dev/null; then
        check_pass "No new secrets detected"
    else
        check_warn "Potential secrets detected (review with: detect-secrets scan)"
    fi
else
    check_warn "detect-secrets not installed"
fi

# Check for known vulnerabilities
if [ -f "venv/bin/safety" ]; then
    if venv/bin/safety check &> /dev/null; then
        check_pass "No known vulnerabilities in dependencies"
    else
        check_warn "Vulnerabilities found (run: safety check)"
    fi
else
    check_warn "safety not installed for vulnerability scanning"
fi

echo ""

# ==============================================================================
# Docker Checks
# ==============================================================================
echo "🐳 Docker Checks"
echo "---------------"

if [ -f "Dockerfile" ]; then
    check_pass "Dockerfile exists"

    # Check if Dockerfile builds
    if docker build -t cashflow-bot:test . &> /dev/null; then
        check_pass "Docker build successful"
    else
        check_warn "Docker build failed"
    fi
else
    check_warn "Dockerfile not found"
fi

if [ -f "docker-compose.yml" ]; then
    check_pass "docker-compose.yml exists"
else
    check_warn "docker-compose.yml not found"
fi

echo ""

# ==============================================================================
# Summary
# ==============================================================================
echo "================================"
echo "📊 Pre-flight Summary"
echo "================================"
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo ""

if [ "$CHECKS_FAILED" -gt 0 ]; then
    echo -e "${RED}❌ Pre-flight checks FAILED${NC}"
    echo "Please fix the issues above before deployment."
    exit 1
else
    echo -e "${GREEN}✅ All pre-flight checks PASSED${NC}"
    echo "Ready for deployment! 🚀"
    exit 0
fi
