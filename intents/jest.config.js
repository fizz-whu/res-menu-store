module.exports = {
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
};