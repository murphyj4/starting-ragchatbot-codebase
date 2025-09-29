#!/bin/bash
# Format code with black and isort

echo "🎨 Formatting code with black..."
uv run black backend/

echo "📦 Sorting imports with isort..."
uv run isort backend/

echo "✅ Formatting complete!"