import { FlowRunner } from '../src/engine/runner';
import { quizSetupFlow } from '../src/flows/quiz_setup';

// Mock fetch globally
global.fetch = jest.fn();

describe('FlowRunner', () => {
  let flowRunner: FlowRunner;

  beforeEach(() => {
    flowRunner = new FlowRunner();
    flowRunner.registerFlow(quizSetupFlow);
    (fetch as jest.Mock).mockClear();
  });

  describe('start', () => {
    it('should start a new quiz setup flow', async () => {
      // Mock budget service response
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ maxQuestions: 50, suggested: 10 })
      });

      const result = await flowRunner.start('quiz_setup', {
        sessionId: 'test-session-1',
        userId: 'user-1',
        subjectId: 'subject-1',
        docIds: ['doc-1', 'doc-2']
      });

      expect(result.sessionId).toBe('test-session-1');
      expect(result.flow).toBe('quiz_setup');
      expect(result.nextPrompt).toContain('What types of questions would you like?');
      expect(result.ui.quick).toEqual(['mcq', 'true_false', 'fill_blank', 'short_answer']);
    });

    it('should handle budget service failure gracefully', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Service unavailable'));

      const result = await flowRunner.start('quiz_setup', {
        sessionId: 'test-session-2',
        userId: 'user-1',
        subjectId: 'subject-1',
        docIds: ['doc-1']
      });

      expect(result.sessionId).toBe('test-session-2');
      expect(result.flow).toBe('quiz_setup');
      // Should use fallback values
      expect(result.nextPrompt).toContain('5 to 50');
    });

    it('should throw error for unknown flow', async () => {
      await expect(
        flowRunner.start('unknown_flow' as any, {
          sessionId: 'test-session-3',
          userId: 'user-1',
          subjectId: 'subject-1',
          docIds: ['doc-1']
        })
      ).rejects.toThrow('Flow not found: unknown_flow');
    });
  });

  describe('ingest', () => {
    let sessionId: string;

    beforeEach(async () => {
      // Mock budget service response
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ maxQuestions: 50, suggested: 10 })
      });

      const startResult = await flowRunner.start('quiz_setup', {
        sessionId: 'test-session-ingest',
        userId: 'user-1',
        subjectId: 'subject-1',
        docIds: ['doc-1']
      });
      sessionId = startResult.sessionId;
    });

    it('should fill question_types slot', async () => {
      const result = await flowRunner.ingest(sessionId, 'mcq and true_false');

      expect(result.stage).toBe('next_slot');
      expect(result.filled.question_types).toEqual(['mcq', 'true_false']);
      expect(result.nextPrompt).toContain('What difficulty level would you prefer?');
      expect(result.ui?.quick).toEqual(['easy', 'medium', 'hard', 'mixed']);
    });

    it('should fill difficulty slot', async () => {
      // First fill question_types
      await flowRunner.ingest(sessionId, 'mcq');
      
      // Then fill difficulty
      const result = await flowRunner.ingest(sessionId, 'hard');

      expect(result.stage).toBe('next_slot');
      expect(result.filled.difficulty).toBe('hard');
      expect(result.nextPrompt).toContain('How many questions would you like?');
    });

    it('should fill requested_count slot and complete flow', async () => {
      // Mock quiz service response
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ quizId: 'quiz-123' })
      });

      // Fill all slots
      await flowRunner.ingest(sessionId, 'mcq');
      await flowRunner.ingest(sessionId, 'medium');
      const result = await flowRunner.ingest(sessionId, '15');

      expect(result.stage).toBe('complete');
      expect(result.done).toBe(true);
      expect(result.filled.requested_count).toBe(15);
    });

    it('should handle out-of-scope input', async () => {
      const result = await flowRunner.ingest(sessionId, 'What is this about?');

      expect(result.stage).toBe('redirect');
      expect(result.nextPrompt).toContain("I'm only here to set up quiz_setup options");
    });

    it('should handle clarification requests', async () => {
      const result = await flowRunner.ingest(sessionId, 'invalid input');

      expect(result.stage).toBe('clarification');
      expect(result.nextPrompt).toContain("I didn't understand that");
    });

    it('should validate and clamp requested_count', async () => {
      // Mock quiz service response
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ quizId: 'quiz-123' })
      });

      // Fill first two slots
      await flowRunner.ingest(sessionId, 'mcq');
      await flowRunner.ingest(sessionId, 'easy');

      // Try to request more than max
      const result = await flowRunner.ingest(sessionId, '100');

      expect(result.stage).toBe('complete');
      expect(result.done).toBe(true);
      // Should be clamped to maxQuestions (50)
      expect(result.filled.requested_count).toBe(50);
    });

    it('should handle invalid question types', async () => {
      const result = await flowRunner.ingest(sessionId, 'invalid_type');

      expect(result.stage).toBe('clarification');
      expect(result.nextPrompt).toContain("I didn't understand that");
    });
  });

  describe('session management', () => {
    it('should retrieve existing session', async () => {
      // Mock budget service response
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ maxQuestions: 50, suggested: 10 })
      });

      const sessionId = 'test-session-retrieve';
      await flowRunner.start('quiz_setup', {
        sessionId,
        userId: 'user-1',
        subjectId: 'subject-1',
        docIds: ['doc-1']
      });

      const session = flowRunner.getSession(sessionId);
      expect(session).toBeDefined();
      expect(session?.sessionId).toBe(sessionId);
      expect(session?.flow).toBe('quiz_setup');
    });

    it('should clear session', async () => {
      // Mock budget service response
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ maxQuestions: 50, suggested: 10 })
      });

      const sessionId = 'test-session-clear';
      await flowRunner.start('quiz_setup', {
        sessionId,
        userId: 'user-1',
        subjectId: 'subject-1',
        docIds: ['doc-1']
      });

      expect(flowRunner.getSession(sessionId)).toBeDefined();
      
      const cleared = flowRunner.clearSession(sessionId);
      expect(cleared).toBe(true);
      expect(flowRunner.getSession(sessionId)).toBeUndefined();
    });

    it('should clear all sessions', async () => {
      // Mock budget service responses
      (fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ maxQuestions: 50, suggested: 10 })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ maxQuestions: 50, suggested: 10 })
        });

      await flowRunner.start('quiz_setup', {
        sessionId: 'test-session-1',
        userId: 'user-1',
        subjectId: 'subject-1',
        docIds: ['doc-1']
      });

      await flowRunner.start('quiz_setup', {
        sessionId: 'test-session-2',
        userId: 'user-2',
        subjectId: 'subject-2',
        docIds: ['doc-2']
      });

      expect(flowRunner.getAllSessions()).toHaveLength(2);
      
      flowRunner.clearAllSessions();
      expect(flowRunner.getAllSessions()).toHaveLength(0);
    });
  });

  describe('idempotency', () => {
    it('should return existing session data on duplicate start', async () => {
      // Mock budget service response
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ maxQuestions: 50, suggested: 10 })
      });

      const sessionMeta = {
        sessionId: 'test-session-idempotent',
        userId: 'user-1',
        subjectId: 'subject-1',
        docIds: ['doc-1']
      };

      const firstResult = await flowRunner.start('quiz_setup', sessionMeta);
      const secondResult = await flowRunner.start('quiz_setup', sessionMeta);

      expect(firstResult.sessionId).toBe(secondResult.sessionId);
      expect(firstResult.flow).toBe(secondResult.flow);
      expect(firstResult.nextPrompt).toBe(secondResult.nextPrompt);
    });
  });
});

