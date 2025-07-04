#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🚀 Setting up test environment for RestaurantHoursIntent...\n');

// Check if AWS credentials are configured
function checkAWSCredentials() {
  const awsCredentialsPath = path.join(process.env.HOME || process.env.USERPROFILE, '.aws', 'credentials');
  const hasCredentials = fs.existsSync(awsCredentialsPath) || 
                        process.env.AWS_ACCESS_KEY_ID || 
                        process.env.AWS_PROFILE;
  
  if (!hasCredentials) {
    console.warn('⚠️  AWS credentials not detected. Integration tests may fail.');
    console.log('   Configure AWS credentials using:');
    console.log('   - aws configure');
    console.log('   - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables');
    console.log('   - Set AWS_PROFILE environment variable\n');
  } else {
    console.log('✅ AWS credentials found\n');
  }
}

// Check if the intent JSON file exists
function checkIntentFile() {
  const intentPath = path.join(__dirname, 'RestaurantInfoIntent.json');
  if (!fs.existsSync(intentPath)) {
    console.error('❌ RestaurantInfoIntent.json not found!');
    console.log('   Make sure the intent JSON file exists in the current directory.\n');
    process.exit(1);
  } else {
    console.log('✅ Intent JSON file found\n');
  }
}

// Create test configuration file
function createTestConfig() {
  const configPath = path.join(__dirname, 'test-config.json');
  
  if (fs.existsSync(configPath)) {
    console.log('✅ Test configuration already exists\n');
    return;
  }
  
  const config = {
    botId: 'RWRKZUM7UP',
    botVersion: 'DRAFT',
    localeId: 'en_US',
    intentName: 'RestaurantHoursIntent',
    botAliasId: 'TSTALIASID',
    region: 'us-east-1',
    testTimeout: 10000,
    skipIntegrationTests: false
  };
  
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log('✅ Created test-config.json');
  console.log('   Update botAliasId with your actual bot alias ID for integration tests\n');
}

// Create Jest configuration
function createJestConfig() {
  const jestConfigPath = path.join(__dirname, 'jest.config.js');
  
  if (fs.existsSync(jestConfigPath)) {
    console.log('✅ Jest configuration already exists\n');
    return;
  }
  
  const jestConfig = `module.exports = {
  testEnvironment: 'node',
  testTimeout: 15000,
  collectCoverageFrom: [
    'tests/**/*.js',
    '!tests/setup/**'
  ],
  testMatch: [
    '**/tests/**/*.test.js'
  ],
  setupFilesAfterEnv: ['<rootDir>/tests/setup/jest.setup.js']
};`;
  
  fs.writeFileSync(jestConfigPath, jestConfig);
  console.log('✅ Created jest.config.js\n');
}

// Create Jest setup file
function createJestSetup() {
  const setupDir = path.join(__dirname, 'tests', 'setup');
  const setupFile = path.join(setupDir, 'jest.setup.js');
  
  if (!fs.existsSync(setupDir)) {
    fs.mkdirSync(setupDir, { recursive: true });
  }
  
  if (fs.existsSync(setupFile)) {
    console.log('✅ Jest setup file already exists\n');
    return;
  }
  
  const setupContent = `// Jest setup file for RestaurantHoursIntent tests

// Set test timeout
jest.setTimeout(15000);

// Mock AWS SDK if credentials are not available
if (!process.env.AWS_ACCESS_KEY_ID && !process.env.AWS_PROFILE) {
  console.warn('AWS credentials not found. Some tests may be skipped.');
}

// Global test configuration
global.TEST_CONFIG = {
  botId: 'RWRKZUM7UP',
  botVersion: 'DRAFT',
  localeId: 'en_US',
  intentName: 'RestaurantHoursIntent',
  region: 'us-east-1'
};`;
  
  fs.writeFileSync(setupFile, setupContent);
  console.log('✅ Created Jest setup file\n');
}

// Create test runner script
function createTestRunner() {
  const runnerPath = path.join(__dirname, 'run-tests.sh');
  
  const runnerContent = `#!/bin/bash

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
`;
  
  fs.writeFileSync(runnerPath, runnerContent);
  
  // Make the script executable (Unix/Linux/Mac)
  if (process.platform !== 'win32') {
    fs.chmodSync(runnerPath, '755');
  }
  
  console.log('✅ Created test runner script (run-tests.sh)\n');
}

// Main setup function
function main() {
  try {
    checkAWSCredentials();
    checkIntentFile();
    createTestConfig();
    createJestConfig();
    createJestSetup();
    createTestRunner();
    
    console.log('🎉 Test environment setup complete!\n');
    console.log('Next steps:');
    console.log('1. npm install                    # Install dependencies');
    console.log('2. Update botAliasId in test-config.json');
    console.log('3. ./run-tests.sh                 # Run all tests');
    console.log('4. npm run test:unit              # Run unit tests only');
    console.log('5. npm run test:integration       # Run integration tests only');
    console.log('6. npm run test:e2e               # Run e2e tests only');
    console.log('7. npm run test:coverage          # Run with coverage report\n');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    process.exit(1);
  }
}

main();