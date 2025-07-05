// Jest setup file for RestaurantHoursIntent tests

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
};