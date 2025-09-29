#!/bin/bash
# Run all code quality checks

set -e

echo "🚀 Running all code quality checks..."
echo ""

# Format check (without modifying files)
echo "1️⃣  Checking code formatting..."
uv run black --check backend/
uv run isort --check-only backend/
echo ""

# Linting
echo "2️⃣  Running linter..."
uv run flake8 backend/ --max-line-length=100 --extend-ignore=E203,W503 --exclude=.venv,__pycache__,chroma_data
echo ""

# Type checking
echo "3️⃣  Running type checker..."
uv run mypy backend/ --config-file=pyproject.toml || echo "⚠️  Type checking found issues (this is informational)"
echo ""

echo "✅ All checks complete!"