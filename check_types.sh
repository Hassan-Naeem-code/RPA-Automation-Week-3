#!/bin/bash
# Type checking script for RPA Inventory Management System
# This script ensures clean mypy runs by clearing cache when needed

echo "🔍 Running MyPy type checking..."

# Clear cache if it exists to avoid cache issues
if [ -d ".mypy_cache" ]; then
    echo "🧹 Clearing mypy cache..."
    rm -rf .mypy_cache
fi

# Run mypy with proper configuration
echo "⚡ Checking types across all source files..."
python -m mypy src/ --ignore-missing-imports

# Check the exit code
if [ $? -eq 0 ]; then
    echo "✅ MyPy type checking passed! No issues found."
    echo "🎉 All 8 source files are type-safe!"
else
    echo "❌ MyPy type checking failed. Please review the errors above."
    exit 1
fi
