import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';

import { flowRunner } from '../engine/runner';
import { quizSetupFlow } from '../flows/quiz_setup';
import { docSummaryFlow } from '../flows/doc_summary';
import { docHighlightsFlow } from '../flows/doc_highlights';
import { docConclusionFlow } from '../flows/doc_conclusion';
import { StartRequest, IngestRequest, ConfirmRequest } from '../engine/flows';
import logger from '../lib/logger';



export async function clarifierRoutes(fastify: FastifyInstance) {
  // Register all flows
  flowRunner.registerFlow(quizSetupFlow);
  flowRunner.registerFlow(docSummaryFlow);
  flowRunner.registerFlow(docHighlightsFlow);
  flowRunner.registerFlow(docConclusionFlow);



  // Start clarification flow
  fastify.post<{ Body: StartRequest }>(
    '/clarifier/start',
    {
      schema: {
        body: {
          type: 'object',
          required: ['sessionId', 'userId', 'subjectId', 'docIds'],
          properties: {
            sessionId: { type: 'string' },
            userId: { type: 'string' },
            subjectId: { type: 'string' },
            docIds: { type: 'array', items: { type: 'string' } },
            flow: { 
              type: 'string', 
              enum: ['quiz_setup', 'doc_summary', 'doc_highlights', 'doc_conclusion'] 
            }
          }
        },
        response: {
          200: {
            type: 'object',
            properties: {
              sessionId: { type: 'string' },
              flow: { type: 'string' },
              nextPrompt: { type: 'string' },
              ui: {
                type: 'object',
                properties: {
                  quick: { type: 'array', items: { type: 'string' } }
                }
              }
            }
          }
        }
      }
    },
    async (request: FastifyRequest<{ Body: StartRequest }>, reply: FastifyReply) => {
      try {
        const { sessionId, userId, subjectId, docIds, flow = 'quiz_setup' } = request.body;

        logger.info('Starting clarification flow', { sessionId, userId, subjectId, docIds, flow });

        // Check if session already exists (idempotency)
        const existingSession = flowRunner.getSession(sessionId);
        if (existingSession) {
          logger.info('Session already exists, returning existing data', { sessionId });
          const currentFlow = existingSession.flow;
          const currentSlot = existingSession.flow === 'quiz_setup' ? 
            quizSetupFlow.slots[existingSession.idx] : null;
          
          if (currentSlot) {
            const nextPrompt = currentSlot.prompt(existingSession.ctx);
            const ui = currentSlot.ui ? currentSlot.ui(existingSession.ctx) : {};
            
            return reply.send({
              sessionId,
              flow: currentFlow,
              nextPrompt,
              ui
            });
          }
        }

        // Start new flow
        const result = await flowRunner.start(flow, {
          sessionId,
          userId,
          subjectId,
          docIds
        });

        reply.send(result);
      } catch (error) {
        logger.error('Error starting clarification flow:', error);
        reply.status(500).send({
          error: 'Failed to start clarification flow',
          message: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
  );

  // Ingest user input for current slot
  fastify.post<{ Body: IngestRequest }>(
    '/clarifier/ingest',
    {
      schema: {
        body: {
          type: 'object',
          required: ['sessionId', 'text'],
          properties: {
            sessionId: { type: 'string' },
            text: { type: 'string' }
          }
        },
        response: {
          200: {
            type: 'object',
            properties: {
              stage: { type: 'string' },
              filled: { type: 'object' },
              nextPrompt: { type: 'string' },
              ui: {
                type: 'object',
                properties: {
                  quick: { type: 'array', items: { type: 'string' } }
                }
              },
              done: { type: 'boolean' }
            }
          }
        }
      }
    },
    async (request: FastifyRequest<{ Body: IngestRequest }>, reply: FastifyReply) => {
      try {
        const { sessionId, text } = request.body;

        logger.info('Processing user input', { sessionId, textLength: text.length });

        const result = await flowRunner.ingest(sessionId, text);

        reply.send(result);
      } catch (error) {
        logger.error('Error processing user input:', error);
        reply.status(500).send({
          error: 'Failed to process user input',
          message: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
  );

  // Confirm study session (backwards compatibility)
  fastify.post<{ Body: ConfirmRequest }>(
    '/clarifier/confirm',
    {
      schema: {
        body: {
          type: 'object',
          required: ['sessionId', 'userId', 'subjectId', 'docIds', 'question_types', 'difficulty', 'requested_count'],
          properties: {
            sessionId: { type: 'string' },
            userId: { type: 'string' },
            subjectId: { type: 'string' },
            docIds: { type: 'array', items: { type: 'string' } },
            question_types: { type: 'array', items: { type: 'string' } },
            difficulty: { type: 'string' },
            requested_count: { type: 'number' }
          }
        },
        response: {
          202: {
            type: 'object',
            properties: {
              sessionId: { type: 'string' },
              accepted: { type: 'boolean' }
            }
          }
        }
      }
    },
    async (request: FastifyRequest<{ Body: ConfirmRequest }>, reply: FastifyReply) => {
      try {
        const { sessionId, userId, subjectId, docIds, question_types, difficulty, requested_count } = request.body;

        logger.info('Confirming study session', { sessionId, userId, subjectId, docIds, question_types, difficulty, requested_count });

        // Check if session exists and is complete
        const session = flowRunner.getSession(sessionId);
        if (!session) {
          return reply.status(404).send({
            error: 'Session not found'
          });
        }

        if (session.flow === 'quiz_setup') {
          // For quiz_setup flow, validate and finalize
          const filled = { question_types, difficulty, requested_count };
          const validation = await quizSetupFlow.validate(filled, session.ctx);
          
          if (!validation.ok) {
            return reply.status(400).send({
              error: 'Invalid confirmation data',
              details: validation.errors
            });
          }

          const result = await quizSetupFlow.finalize({
            ...validation.filled,
            sessionId: session.sessionId,
            userId: session.userId,
            subjectId: session.subjectId,
            docIds: session.docIds
          }, session.ctx);
          
          // Mark session as complete
          session.filled = validation.filled;
          session.idx = -1;

          return reply.status(result.status).send(result.body);
        } else {
          // For other flows, return 501
          return reply.status(501).send({
            error: 'Flow not yet implemented',
            flow: session.flow
          });
        }
      } catch (error) {
        logger.error('Error confirming study session:', error);
        reply.status(500).send({
          error: 'Failed to confirm study session',
          message: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
  );
}
