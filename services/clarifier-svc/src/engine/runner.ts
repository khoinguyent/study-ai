import { SessionState, FlowSpec } from './flows';
import { getParserByType, isOutOfScope } from './parsers';
import { llmExtractor } from './extractor';
import logger from '../lib/logger';

export class FlowRunner {
  private sessions: Map<string, SessionState> = new Map();
  private flows: Map<string, FlowSpec> = new Map();

  constructor() {}

  registerFlow(flow: FlowSpec): void {
    this.flows.set(flow.id, flow);
    logger.info(`Registered flow: ${flow.id}`);
  }

  async start(flowId: string, sessionMeta: {
    sessionId: string;
    userId: string;
    subjectId: string;
    docIds: string[];
  }): Promise<{
    sessionId: string;
    flow: string;
    nextPrompt: string;
    ui: { quick?: string[] };
  }> {
    const flow = this.flows.get(flowId);
    if (!flow) {
      throw new Error(`Flow not found: ${flowId}`);
    }

    // Initialize flow context
    const ctx = await flow.init(sessionMeta);
    
    // Create session state
    const session: SessionState = {
      ...sessionMeta,
      flow: flowId as FlowSpec['id'],
      ctx,
      filled: {},
      idx: 0
    };

    this.sessions.set(sessionMeta.sessionId, session);
    logger.info(`Started session ${sessionMeta.sessionId} with flow ${flowId}`);

    // Get first slot prompt
    const currentSlot = flow.slots[0];
    if (!currentSlot) {
      throw new Error(`Flow ${flowId} has no slots defined`);
    }

    const nextPrompt = currentSlot.prompt(ctx);
    const ui = currentSlot.ui ? currentSlot.ui(ctx) : {};

    return {
      sessionId: sessionMeta.sessionId,
      flow: flowId,
      nextPrompt,
      ui
    };
  }

  async ingest(sessionId: string, text: string): Promise<{
    stage: string;
    filled: Record<string, any>;
    nextPrompt?: string;
    ui?: { quick?: string[] };
    done?: boolean;
    finalizeResult?: any;
  }> {
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }

    const flow = this.flows.get(session.flow);
    if (!flow) {
      throw new Error(`Flow not found: ${session.flow}`);
    }

    // Check if text is out of scope
    if (isOutOfScope(text)) {
      return {
        stage: 'redirect',
        filled: session.filled,
        nextPrompt: `I'm only here to set up ${session.flow} options. Please focus on that.`
      };
    }

    const currentSlot = flow.slots[session.idx];
    if (!currentSlot) {
      // All slots filled, validate and finalize
      const validation = await flow.validate(session.filled, session.ctx);
      if (!validation.ok) {
        return {
          stage: 'error',
          filled: session.filled,
          nextPrompt: `There are some issues: ${validation.errors?.join(', ')}. Please try again.`
        };
      }

      // Finalize the flow
      // Note: finalize method should not trigger notifications
      const finalizeResult = await flow.finalize(validation.filled, session.ctx);
      
      // Mark session as done
      session.filled = validation.filled;
      session.idx = -1; // Mark as complete
      
      // Return completion status without triggering notifications
      return {
        stage: 'complete',
        filled: session.filled,
        done: true,
        finalizeResult: finalizeResult // Include the result from finalize
      };
    }

    // Try to parse the current slot
    let parsedValue: any = null;
    
    // First try deterministic parser
    const parser = getParserByType(currentSlot.type, currentSlot.parserHint);
    if (parser) {
      try {
        if (currentSlot.type === 'multi_enum' || currentSlot.type === 'enum') {
          parsedValue = (parser as any)(text, currentSlot.allowed || []);
        } else if (currentSlot.type === 'int') {
          parsedValue = (parser as any)(text, { 
            min: currentSlot.min || 0, 
            max: currentSlot.max || Number.MAX_SAFE_INTEGER 
          });
        } else {
          parsedValue = (parser as any)(text);
        }
      } catch (error) {
        logger.warn(`Deterministic parser failed for slot ${currentSlot.key}:`, error);
      }
    }

    // If deterministic parser failed and LLM extractor is enabled, try that
    if (parsedValue === null && llmExtractor.isEnabled()) {
      try {
        const extracted = await llmExtractor.extract(text, currentSlot.key, currentSlot.parserHint);
        
        // Map extracted values to current slot
        if (currentSlot.key === 'question_types' && extracted['question_types']) {
          parsedValue = extracted['question_types'];
        } else if (currentSlot.key === 'difficulty' && extracted['difficulty']) {
          parsedValue = extracted['difficulty'];
        } else if (currentSlot.key === 'requested_count' && extracted['requested_count']) {
          parsedValue = extracted['requested_count'];
        } else if (extracted['count']) {
          parsedValue = extracted['count'];
        }
        
        // Check if out of scope
        if (extracted.out_of_scope) {
          return {
            stage: 'redirect',
            filled: session.filled,
            nextPrompt: `I'm only here to set up ${session.flow} options. Please focus on that.`
          };
        }
      } catch (error) {
        logger.warn(`LLM extractor failed for slot ${currentSlot.key}:`, error);
      }
    }

    // If we still don't have a value, ask for clarification
    if (parsedValue === null) {
      return {
        stage: 'clarification',
        filled: session.filled,
        nextPrompt: `I didn't understand that. ${currentSlot.prompt(session.ctx)}`
      };
    }

    // Validate the parsed value
    let isValid = true;
    let errorMessage = '';

    if (currentSlot.type === 'multi_enum' || currentSlot.type === 'enum') {
      if (currentSlot.allowed) {
        if (currentSlot.type === 'multi_enum') {
          isValid = Array.isArray(parsedValue) && 
                   parsedValue.every(v => currentSlot.allowed!.includes(v));
        } else {
          isValid = currentSlot.allowed.includes(parsedValue);
        }
        if (!isValid) {
          errorMessage = `Please choose from: ${currentSlot.allowed.join(', ')}`;
        }
      }
    } else if (currentSlot.type === 'int') {
      if (currentSlot.min !== undefined && parsedValue < currentSlot.min) {
        isValid = false;
        errorMessage = `Minimum value is ${currentSlot.min}`;
      } else if (currentSlot.max !== undefined && parsedValue > currentSlot.max) {
        isValid = false;
        errorMessage = `Maximum value is ${currentSlot.max}`;
      }
    }

    if (!isValid) {
      return {
        stage: 'error',
        filled: session.filled,
        nextPrompt: errorMessage
      };
    }

    // Slot is filled successfully
    session.filled[currentSlot.key] = parsedValue;
    session.idx++;

    logger.info(`Slot ${currentSlot.key} filled with value:`, parsedValue);

    // Check if all slots are filled
    if (session.idx >= flow.slots.length) {
      // All slots filled, validate and finalize
      const validation = await flow.validate(session.filled, session.ctx);
      if (!validation.ok) {
        return {
          stage: 'error',
          filled: session.filled,
          nextPrompt: `There are some issues: ${validation.errors?.join(', ')}. Please try again.`
        };
      }

      // Finalize the flow
      // Note: finalize method should not trigger notifications
      const finalizeResult = await flow.finalize(validation.filled, session.ctx);
      
      // Mark session as done
      session.filled = validation.filled;
      session.idx = -1; // Mark as complete
      
      // Return completion status without triggering notifications
      return {
        stage: 'complete',
        filled: session.filled,
        done: true,
        finalizeResult: finalizeResult // Include the result from finalize
      };
    }

    // Get next slot prompt
    const nextSlot = flow.slots[session.idx];
    if (!nextSlot) {
      throw new Error(`No slot found at index ${session.idx}`);
    }
    const nextPrompt = nextSlot.prompt(session.ctx);
    const ui = nextSlot.ui ? nextSlot.ui(session.ctx) : {};

    return {
      stage: 'next_slot',
      filled: session.filled,
      nextPrompt,
      ui
    };
  }

  getSession(sessionId: string): SessionState | undefined {
    return this.sessions.get(sessionId);
  }

  getAllSessions(): SessionState[] {
    return Array.from(this.sessions.values());
  }

  clearSession(sessionId: string): boolean {
    return this.sessions.delete(sessionId);
  }

  clearAllSessions(): void {
    this.sessions.clear();
  }
}

export const flowRunner = new FlowRunner();
