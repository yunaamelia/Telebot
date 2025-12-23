#!/usr/bin/env bash
# Pre-build hook - Run before building Docker image
# Usage: ./scripts/pre-build.sh

set -e

echo "🔨 Running pre-build checks..."

# Verify all required files exist
REQUIRED_FILES=(
    "Dockerfile"
    "requirements.txt"
    ".dockerignore"
    "src/config/settings.py"
    "alembic.ini"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done

echo "✅ All required files present"

# Run linting
echo "🔍 Running linters..."
if command -v flake8 &> /dev/null; then
    flake8 src/ --max-line-length=100 --exclude=migrations
    echo "✅ Linting passed"
fi

# Check for secrets
echo "🔒 Checking for secrets..."
if command -v detect-secrets &> /dev/null; then
    detect-secrets scan --baseline .secrets.baseline
    echo "✅ No secrets detected"
fi

# Verify dependencies
echo "📦 Verifying dependencies..."
if [ -f "venv/bin/pip" ]; then
    venv/bin/pip check
    echo "✅ Dependencies verified"
fi

echo "✅ Pre-build checks completed"
