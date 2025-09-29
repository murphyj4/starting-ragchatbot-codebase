#!/bin/bash
# Run linting checks with flake8

echo "🔍 Running flake8..."
uv run flake8 backend/ --max-line-length=100 --extend-ignore=E203,W503 --exclude=.venv,__pycache__,chroma_data

if [ $? -eq 0 ]; then
    echo "✅ Linting passed!"
else
    echo "❌ Linting failed!"
    exit 1
fi