#!/usr/bin/env bash
# Git pre-push hook - Additional checks before pushing
# Installed automatically via pre-commit

set -e

echo "🔄 Running pre-push checks..."

# Run tests with coverage
echo "  📊 Running test suite with coverage..."
if pytest --cov=src --cov-report=term-missing:skip-covered --cov-fail-under=80 -q; then
    echo "  ✅ Tests passed with adequate coverage"
else
    echo "  ❌ Tests failed or coverage below 80%"
    exit 1
fi

# Check for uncommitted changes
if ! git diff --quiet; then
    echo "  ⚠️  Warning: You have uncommitted changes"
fi

echo "  ✅ Pre-push checks completed"
