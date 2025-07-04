const fs = require('fs');
const path = require('path');

describe('RestaurantHoursIntent Configuration Tests', () => {
  let intentConfig;

  beforeAll(() => {
    const intentPath = path.join(__dirname, '../../RestaurantInfoIntent.json');
    intentConfig = JSON.parse(fs.readFileSync(intentPath, 'utf8'));
  });

  test('should have correct intent name', () => {
    expect(intentConfig.intentName).toBe('RestaurantHoursIntent');
  });

  test('should have appropriate description', () => {
    expect(intentConfig.description).toBe('Intent to provide restaurant hours information');
  });

  test('should have sample utterances', () => {
    expect(intentConfig.sampleUtterances).toBeDefined();
    expect(Array.isArray(intentConfig.sampleUtterances)).toBe(true);
    expect(intentConfig.sampleUtterances.length).toBeGreaterThan(0);
  });

  test('should contain hours-related utterances', () => {
    const utterances = intentConfig.sampleUtterances.map(u => u.utterance.toLowerCase());
    
    const expectedKeywords = ['hours', 'open', 'close', 'time'];
    expectedKeywords.forEach(keyword => {
      const hasKeyword = utterances.some(utterance => utterance.includes(keyword));
      expect(hasKeyword).toBe(true);
    });
  });

  test('should have valid utterance structure', () => {
    intentConfig.sampleUtterances.forEach(utterance => {
      expect(utterance).toHaveProperty('utterance');
      expect(typeof utterance.utterance).toBe('string');
      expect(utterance.utterance.length).toBeGreaterThan(0);
    });
  });

  test('should have closing response configured', () => {
    expect(intentConfig.intentClosingSetting).toBeDefined();
    expect(intentConfig.intentClosingSetting.closingResponse).toBeDefined();
    expect(intentConfig.intentClosingSetting.closingResponse.messageGroups).toBeDefined();
  });

  test('should have appropriate closing response message', () => {
    const messageGroups = intentConfig.intentClosingSetting.closingResponse.messageGroups;
    expect(messageGroups.length).toBeGreaterThan(0);
    
    const message = messageGroups[0].message.plainTextMessage.value;
    expect(message).toContain('11:00 AM');
    expect(message).toContain('10:00 PM');
    expect(message).toContain('Monday');
    expect(message).toContain('Sunday');
  });

  test('should not have conflicting intent configurations', () => {
    // Should not have fulfillment code hook since we're using closing response
    expect(intentConfig.fulfillmentCodeHook).toBeUndefined();
  });

  test('should have valid JSON structure', () => {
    expect(() => {
      JSON.stringify(intentConfig);
    }).not.toThrow();
  });
});