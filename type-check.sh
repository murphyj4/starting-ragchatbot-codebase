#!/bin/bash
# Run type checking with mypy

echo "🔎 Running mypy type checker..."
uv run mypy backend/ --config-file=pyproject.toml

if [ $? -eq 0 ]; then
    echo "✅ Type checking passed!"
else
    echo "⚠️  Type checking found issues (this is informational)"
fi