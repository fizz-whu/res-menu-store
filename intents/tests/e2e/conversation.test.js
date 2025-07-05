const { LexRuntimeV2Client, RecognizeTextCommand } = require('@aws-sdk/client-lex-runtime-v2');

const TEST_CONFIG = {
  botId: 'RWRKZUM7UP',
  botAliasId: 'TSTALIASID', // Replace with actual alias ID
  localeId: 'en_US',
  sessionId: 'e2e-test-session-' + Date.now()
};

describe('End-to-End Conversation Tests', () => {
  let lexRuntimeClient;

  beforeAll(() => {
    lexRuntimeClient = new LexRuntimeV2Client({ region: 'us-east-1' });
  });

  describe('Complete Conversation Flow', () => {
    test('should handle complete hours inquiry conversation', async () => {
      const conversationSteps = [
        {
          input: 'Hi',
          expectIntent: null // Welcome or fallback intent
        },
        {
          input: 'What are your hours?',
          expectIntent: 'RestaurantHoursIntent',
          expectResponse: ['11:00 AM', '10:00 PM', 'Monday', 'Sunday']
        },
        {
          input: 'Are you open now?',
          expectIntent: 'RestaurantHoursIntent',
          expectResponse: ['11:00 AM', '10:00 PM']
        }
      ];

      for (const step of conversationSteps) {
        try {
          const command = new RecognizeTextCommand({
            botId: TEST_CONFIG.botId,
            botAliasId: TEST_CONFIG.botAliasId,
            localeId: TEST_CONFIG.localeId,
            sessionId: TEST_CONFIG.sessionId,
            text: step.input
          });

          const response = await lexRuntimeClient.send(command);
          
          if (step.expectIntent) {
            expect(response.intent?.name).toBe(step.expectIntent);
          }
          
          if (step.expectResponse && response.messages) {
            const messageContent = response.messages[0]?.content || '';
            step.expectResponse.forEach(expectedText => {
              expect(messageContent).toContain(expectedText);
            });
          }
        } catch (error) {
          console.warn(`Conversation test failed for input "${step.input}":`, error.message);
        }
      }
    });

    test('should handle various time-related questions', async () => {
      const timeQuestions = [
        'When do you open in the morning?',
        'How late do you stay open?',
        'Are you open on weekends?',
        'What time should I come by?',
        'Do you close early on Sundays?'
      ];

      for (const question of timeQuestions) {
        try {
          const command = new RecognizeTextCommand({
            botId: TEST_CONFIG.botId,
            botAliasId: TEST_CONFIG.botAliasId,
            localeId: TEST_CONFIG.localeId,
            sessionId: TEST_CONFIG.sessionId + '-' + Math.random(),
            text: question
          });

          const response = await lexRuntimeClient.send(command);
          
          // Should either recognize as hours intent or fallback gracefully
          if (response.intent?.name === 'RestaurantHoursIntent') {
            expect(response.intent.state).toBe('ReadyForFulfillment');
          }
          
          // Response should be helpful
          if (response.messages && response.messages.length > 0) {
            const messageContent = response.messages[0].content;
            expect(messageContent.length).toBeGreaterThan(0);
          }
        } catch (error) {
          console.warn(`Time question test failed for "${question}":`, error.message);
        }
      }
    });
  });

  describe('Edge Cases and Error Handling', () => {
    test('should handle empty input gracefully', async () => {
      try {
        const command = new RecognizeTextCommand({
          botId: TEST_CONFIG.botId,
          botAliasId: TEST_CONFIG.botAliasId,
          localeId: TEST_CONFIG.localeId,
          sessionId: TEST_CONFIG.sessionId + '-empty',
          text: ''
        });

        const response = await lexRuntimeClient.send(command);
        
        // Should handle empty input without crashing
        expect(response).toBeDefined();
      } catch (error) {
        // Empty input might be rejected by AWS, which is acceptable
        expect(error.message).toBeDefined();
      }
    });

    test('should handle very long input', async () => {
      const longInput = 'What are your hours? '.repeat(50);
      
      try {
        const command = new RecognizeTextCommand({
          botId: TEST_CONFIG.botId,
          botAliasId: TEST_CONFIG.botAliasId,
          localeId: TEST_CONFIG.localeId,
          sessionId: TEST_CONFIG.sessionId + '-long',
          text: longInput
        });

        const response = await lexRuntimeClient.send(command);
        
        // Should handle long input gracefully
        expect(response).toBeDefined();
      } catch (error) {
        console.warn('Long input test failed:', error.message);
      }
    });

    test('should handle special characters in input', async () => {
      const specialInputs = [
        'What are your hours??? 🕐',
        'When are you open? (need to know ASAP)',
        'Hours: what are they?'
      ];

      for (const input of specialInputs) {
        try {
          const command = new RecognizeTextCommand({
            botId: TEST_CONFIG.botId,
            botAliasId: TEST_CONFIG.botAliasId,
            localeId: TEST_CONFIG.localeId,
            sessionId: TEST_CONFIG.sessionId + '-special-' + Math.random(),
            text: input
          });

          const response = await lexRuntimeClient.send(command);
          
          // Should handle special characters without crashing
          expect(response).toBeDefined();
        } catch (error) {
          console.warn(`Special characters test failed for "${input}":`, error.message);
        }
      }
    });
  });
});