#!/usr/bin/env bash
# Quick verification script for hooks installation
# Usage: ./scripts/verify-hooks.sh

set -e

echo "🔍 Verifying Git Hooks Installation..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0

check() {
    if [ "$1" -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}❌ $2${NC}"
        ((CHECKS_FAILED++))
    fi
}

# Check pre-commit installation
if command -v pre-commit &> /dev/null; then
    check 0 "pre-commit is installed"
    PRE_COMMIT_VERSION=$(pre-commit --version)
    echo "   Version: $PRE_COMMIT_VERSION"
else
    check 1 "pre-commit not installed (run: pip install pre-commit)"
fi

# Check if hooks are installed
if [ -f ".git/hooks/pre-commit" ]; then
    check 0 "pre-commit hook installed"
else
    check 1 "pre-commit hook not installed (run: make install-hooks)"
fi

if [ -f ".git/hooks/pre-push" ]; then
    check 0 "pre-push hook installed"
else
    check 1 "pre-push hook not installed (run: make install-hooks)"
fi

if [ -f ".git/hooks/commit-msg" ]; then
    check 0 "commit-msg hook installed"
else
    check 1 "commit-msg hook not installed (run: make install-hooks)"
fi

# Check configuration files
if [ -f ".pre-commit-config.yaml" ]; then
    check 0 ".pre-commit-config.yaml exists"
    HOOK_COUNT=$(grep -c "^  - id:" .pre-commit-config.yaml || true)
    echo "   Configured hooks: $HOOK_COUNT"
else
    check 1 ".pre-commit-config.yaml missing"
fi

if [ -f ".bandit.yml" ]; then
    check 0 ".bandit.yml exists"
else
    check 1 ".bandit.yml missing"
fi

if [ -f ".secrets.baseline" ]; then
    check 0 ".secrets.baseline exists"
else
    check 1 ".secrets.baseline missing"
fi

# Check scripts
SCRIPT_COUNT=0
for script in check_env_example.py check_todos.py preflight.sh pre-build.sh pre-push.sh post-merge.sh; do
    if [ -f "scripts/$script" ]; then
        ((SCRIPT_COUNT++))
    fi
done

if [ "$SCRIPT_COUNT" -eq 6 ]; then
    check 0 "All 6 custom scripts present"
else
    check 1 "Some scripts missing ($SCRIPT_COUNT/6 found)"
fi

# Check documentation
DOC_COUNT=0
for doc in HOOKS.md HOOKS_QUICKSTART.md HOOKS_IMPLEMENTATION_SUMMARY.md; do
    if [ -f "docs/$doc" ]; then
        ((DOC_COUNT++))
    fi
done

if [ "$DOC_COUNT" -eq 3 ]; then
    check 0 "All 3 documentation files present"
else
    check 1 "Some documentation missing ($DOC_COUNT/3 found)"
fi

# Check if Makefile has hooks target
if grep -q "install-hooks:" Makefile 2>/dev/null; then
    check 0 "Makefile has install-hooks target"
else
    check 1 "Makefile missing install-hooks target"
fi

echo ""
echo "================================"
if [ "$CHECKS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed ($CHECKS_PASSED/$CHECKS_PASSED)${NC}"
    echo ""
    echo "Git hooks are properly installed! 🎉"
    echo ""
    echo "Try running:"
    echo "  pre-commit run --all-files"
    echo "  make lint"
    echo "  ./scripts/preflight.sh"
else
    echo -e "${RED}❌ Some checks failed${NC}"
    echo "Passed: $CHECKS_PASSED"
    echo "Failed: $CHECKS_FAILED"
    echo ""
    echo "To fix, run:"
    echo "  make install-hooks"
fi
echo "================================"
