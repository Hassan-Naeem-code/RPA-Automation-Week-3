#!/bin/bash
# Type checking script for RPA Inventory Management System
# This script runs MyPy type checking with proper configuration

echo "🔍 Running MyPy type checking..."

# Run mypy with proper configuration
echo "⚡ Checking types across all 8 source files..."
python -m mypy src/ --ignore-missing-imports

# Check the exit code
if [ $? -eq 0 ]; then
    echo "✅ MyPy type checking passed! No issues found."
    echo "🎉 All 8 source files are type-safe!"
    echo "🛡️  Type ignore comments handle external library stubs gracefully"
else
    echo "❌ MyPy type checking failed. Please review the errors above."
    exit 1
fi
