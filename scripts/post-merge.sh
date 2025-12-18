#!/usr/bin/env bash
# Post-merge hook - Run after git merge or pull
# Install: ln -s ../../scripts/post-merge.sh .git/hooks/post-merge

set -e

echo "🔄 Running post-merge tasks..."

# Check if requirements changed
if git diff HEAD@{1} --stat -- requirements.txt requirements-dev.txt | grep .; then
    echo "📦 Requirements changed - updating dependencies..."
    if [ -d "venv" ]; then
        venv/bin/pip install -r requirements.txt -r requirements-dev.txt
        echo "✅ Dependencies updated"
    else
        echo "⚠️  Virtual environment not found - please run: python3 -m venv venv"
    fi
fi

# Check if migrations changed
if git diff HEAD@{1} --stat -- migrations/versions/ | grep .; then
    echo "🗄️  Migrations changed - consider running: alembic upgrade head"
fi

# Check if .env.example changed
if git diff HEAD@{1} --stat -- .env.example | grep .; then
    echo "⚙️  .env.example changed - please review and update your .env file"
fi

echo "✅ Post-merge tasks completed"
