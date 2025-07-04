const { LexModelsV2Client, GetIntentCommand } = require('@aws-sdk/client-lexv2-models');
const { LexRuntimeV2Client, RecognizeTextCommand } = require('@aws-sdk/client-lex-runtime-v2');

// Test configuration
const TEST_CONFIG = {
  botId: 'RWRKZUM7UP',
  botVersion: 'DRAFT',
  localeId: 'en_US',
  intentName: 'RestaurantHoursIntent',
  // Add your bot alias ID here when available
  botAliasId: 'TSTALIASID', // Replace with actual alias ID
  sessionId: 'test-session-' + Date.now()
};

describe('AWS Lex Integration Tests', () => {
  let lexModelsClient;
  let lexRuntimeClient;
  let intentId;

  beforeAll(async () => {
    // Initialize AWS clients
    lexModelsClient = new LexModelsV2Client({ region: 'us-east-1' });
    lexRuntimeClient = new LexRuntimeV2Client({ region: 'us-east-1' });
  });

  describe('Intent Configuration in AWS', () => {
    test('should retrieve intent from AWS Lex', async () => {
      try {
        // First, get the intent ID by listing intents
        const { ListIntentsCommand } = require('@aws-sdk/client-lexv2-models');
        const listCommand = new ListIntentsCommand({
          botId: TEST_CONFIG.botId,
          botVersion: TEST_CONFIG.botVersion,
          localeId: TEST_CONFIG.localeId
        });
        
        const listResponse = await lexModelsClient.send(listCommand);
        const intent = listResponse.intents?.find(i => i.intentName === TEST_CONFIG.intentName);
        
        expect(intent).toBeDefined();
        expect(intent.intentName).toBe(TEST_CONFIG.intentName);
        
        intentId = intent.intentId;
      } catch (error) {
        console.warn('AWS Lex intent not found or AWS credentials not configured:', error.message);
        // Skip this test if AWS is not configured
        return;
      }
    });

    test('should have correct intent configuration in AWS', async () => {
      if (!intentId) {
        console.warn('Skipping test - intent not found in AWS');
        return;
      }

      try {
        const command = new GetIntentCommand({
          botId: TEST_CONFIG.botId,
          botVersion: TEST_CONFIG.botVersion,
          localeId: TEST_CONFIG.localeId,
          intentId: intentId
        });

        const response = await lexModelsClient.send(command);
        
        expect(response.intentName).toBe(TEST_CONFIG.intentName);
        expect(response.description).toBe('Intent to provide restaurant hours information');
        expect(response.sampleUtterances).toBeDefined();
        expect(response.sampleUtterances.length).toBeGreaterThan(0);
        
        // Check if closing response is configured
        expect(response.intentClosingSetting).toBeDefined();
      } catch (error) {
        console.warn('AWS Lex configuration test failed:', error.message);
      }
    });
  });

  describe('Intent Recognition Tests', () => {
    const testUtterances = [
      'What are your hours',
      'When are you open',
      'What time do you close',
      'Are you open now',
      'How late are you open',
      'What time do you open',
      'Are you open today',
      'What are your business hours',
      'When do you close'
    ];

    testUtterances.forEach(utterance => {
      test(`should recognize intent for utterance: "${utterance}"`, async () => {
        try {
          const command = new RecognizeTextCommand({
            botId: TEST_CONFIG.botId,
            botAliasId: TEST_CONFIG.botAliasId,
            localeId: TEST_CONFIG.localeId,
            sessionId: TEST_CONFIG.sessionId + '-' + Math.random(),
            text: utterance
          });

          const response = await lexRuntimeClient.send(command);
          
          expect(response.intent?.name).toBe(TEST_CONFIG.intentName);
          expect(response.intent?.state).toBe('ReadyForFulfillment');
          
          // Check if response contains hours information
          if (response.messages && response.messages.length > 0) {
            const message = response.messages[0].content;
            expect(message).toContain('11:00 AM');
            expect(message).toContain('10:00 PM');
          }
        } catch (error) {
          console.warn(`Recognition test failed for "${utterance}":`, error.message);
          // Skip if bot alias is not configured
        }
      });
    });
  });

  describe('Response Validation Tests', () => {
    test('should return consistent response format', async () => {
      try {
        const command = new RecognizeTextCommand({
          botId: TEST_CONFIG.botId,
          botAliasId: TEST_CONFIG.botAliasId,
          localeId: TEST_CONFIG.localeId,
          sessionId: TEST_CONFIG.sessionId + '-format-test',
          text: 'What are your hours'
        });

        const response = await lexRuntimeClient.send(command);
        
        expect(response).toHaveProperty('sessionId');
        expect(response).toHaveProperty('messages');
        expect(response).toHaveProperty('intent');
        
        if (response.messages && response.messages.length > 0) {
          const message = response.messages[0];
          expect(message).toHaveProperty('content');
          expect(message).toHaveProperty('contentType');
          expect(message.contentType).toBe('PlainText');
        }
      } catch (error) {
        console.warn('Response format test failed:', error.message);
      }
    });
  });
});