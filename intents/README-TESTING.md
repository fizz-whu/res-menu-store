# RestaurantHoursIntent Testing Guide

This comprehensive test suite validates your RestaurantHoursIntent from multiple angles to minimize manual testing.

## Test Types

### 1. Unit Tests (`tests/unit/`)
- **Intent Configuration**: Validates JSON structure, utterances, and response configuration
- **Coverage**: Intent name, description, sample utterances, closing responses
- **Fast execution**: No AWS API calls

### 2. Integration Tests (`tests/integration/`)
- **AWS Lex API**: Tests actual intent deployment and configuration in AWS
- **Intent Recognition**: Validates that AWS Lex correctly identifies the intent
- **Response Validation**: Ensures proper response format and content

### 3. End-to-End Tests (`tests/e2e/`)
- **Complete Conversations**: Tests full conversation flows
- **Edge Cases**: Handles empty input, long text, special characters
- **Real User Scenarios**: Simulates actual user interactions

## Quick Start

```bash
# 1. Set up test environment
node setup-test-env.js

# 2. Install dependencies
npm install

# 3. Update configuration
# Edit test-config.json with your actual bot alias ID

# 4. Run all tests
./run-tests.sh

# Or run specific test types
npm run test:unit          # Unit tests only
npm run test:integration   # Integration tests only  
npm run test:e2e          # End-to-end tests only
npm run test:coverage     # With coverage report
```

## Prerequisites

### AWS Configuration
Integration and E2E tests require AWS credentials:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1

# Option 3: AWS Profile
export AWS_PROFILE=your-profile-name
```

### Bot Configuration
Update `test-config.json` with your actual values:

```json
{
  "botId": "RWRKZUM7UP",
  "botAliasId": "YOUR_ACTUAL_ALIAS_ID",
  "localeId": "en_US",
  "region": "us-east-1"
}
```

## Test Coverage

### What's Tested

✅ **Intent Configuration**
- JSON structure validation
- Required fields present
- Utterances contain hours-related keywords
- Closing response configured correctly

✅ **AWS Lex Integration**
- Intent exists in AWS Lex
- Configuration matches local JSON
- Intent recognition works for all sample utterances
- Response format is correct

✅ **Conversation Flow**
- Complete conversation scenarios
- Multiple question types about hours
- Edge cases (empty input, long text, special characters)
- Error handling

✅ **Response Quality**
- Contains correct hours (11:00 AM - 10:00 PM)
- Mentions all days (Monday - Sunday)
- Consistent response format
- Helpful and clear messaging

### Sample Test Utterances

The tests validate recognition for:
- "What are your hours"
- "When are you open"
- "What time do you close"
- "Are you open now"
- "How late are you open"
- "What time do you open"
- "Are you open today"
- "What are your business hours"
- "When do you close"

Plus edge cases and variations.

## Running Tests

### All Tests
```bash
./run-tests.sh
```

### Individual Test Suites
```bash
# Unit tests (fast, no AWS required)
npm run test:unit

# Integration tests (requires AWS)
npm run test:integration

# E2E tests (requires AWS bot alias)
npm run test:e2e

# With coverage report
npm run test:coverage

# Watch mode for development
npm run test:watch
```

## Test Results

### Success Indicators
- ✅ All unit tests pass (JSON configuration valid)
- ✅ Integration tests pass (intent deployed correctly)
- ✅ E2E tests pass (conversations work end-to-end)
- ✅ Coverage report shows high test coverage

### Common Issues

**Unit Tests Failing**
- Check RestaurantInfoIntent.json syntax
- Verify intent name is "RestaurantHoursIntent"
- Ensure closing response is configured

**Integration Tests Failing**
- Verify AWS credentials are configured
- Check bot ID is correct (RWRKZUM7UP)
- Ensure intent is deployed in AWS Lex

**E2E Tests Failing**
- Update botAliasId in test-config.json
- Verify bot alias is deployed and active
- Check AWS region settings

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Run Intent Tests
  run: |
    cd intents
    npm install
    npm run test:unit
    npm run test:integration
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

## Test Automation Benefits

This comprehensive test suite provides:

1. **Confidence**: Validates intent works before deployment
2. **Speed**: Automated testing is faster than manual testing
3. **Coverage**: Tests scenarios you might miss manually
4. **Regression**: Catches breaking changes early
5. **Documentation**: Tests serve as living documentation

## Troubleshooting

### AWS Credentials Issues
```bash
# Check AWS credentials
aws sts get-caller-identity

# List your Lex bots
aws lexv2-models list-bots
```

### Test Failures
- Check AWS region (default: us-east-1)
- Verify bot and intent IDs are correct
- Ensure intent is built and deployed in AWS Lex
- Check network connectivity to AWS

### Performance Issues
- Unit tests should run in seconds
- Integration tests may take 10-30 seconds
- E2E tests can take 30-60 seconds

Run tests individually to isolate issues:
```bash
npx jest tests/unit/intent-config.test.js
npx jest tests/integration/lex-api.test.js
npx jest tests/e2e/conversation.test.js
```