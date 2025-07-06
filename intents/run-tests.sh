#!/bin/bash

echo "🧪 Running RestaurantHoursIntent Test Suite"
echo "=========================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js first."
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Run different test suites
echo ""
echo "🔧 Running Unit Tests..."
npm run test:unit

echo ""
echo "🔗 Running Integration Tests..."
npm run test:integration

echo ""
echo "🌐 Running E2E Tests..."
npm run test:e2e

echo ""
echo "📊 Running Coverage Report..."
npm run test:coverage

echo ""
echo "✅ All tests completed!"
