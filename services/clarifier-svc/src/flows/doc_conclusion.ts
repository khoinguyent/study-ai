import { FlowSpec } from '../engine/flows';

export const docConclusionFlow: FlowSpec = {
  id: 'doc_conclusion',
  
  async init(_ctx: any) {
    // No dynamic initialization needed for now
    return {
      allowedLengths: ['short', 'medium']
    };
  },

  slots: [
    {
      key: 'thesis',
      type: 'string',
      prompt: (_ctx: any) => `What is the main thesis or argument you want the conclusion to support?`,
      required: true
    },
    {
      key: 'length',
      type: 'enum',
      prompt: (ctx: any) => `How long should the conclusion be? Choose from: ${ctx.allowedLengths.join(', ')}`,
      ui: (ctx: any) => ({
        quick: ctx.allowedLengths
      }),
      allowed: ['short', 'medium'],
      required: true,
      parserHint: 'length'
    }
  ],

  async validate(filled: Record<string, any>, ctx: any) {
    const errors: string[] = [];

    if (!filled['thesis'] || typeof filled['thesis'] !== 'string' || filled['thesis'].trim().length === 0) {
      errors.push('Thesis statement is required');
    }

    if (!filled['length'] || !ctx.allowedLengths.includes(filled['length'])) {
      errors.push(`Length must be one of: ${ctx.allowedLengths.join(', ')}`);
    }

    if (errors.length > 0) {
      return { ok: false, errors, filled };
    }

    return { ok: true, filled };
  },

  async finalize(_filled: Record<string, any>, _ctx: any) {
    return {
      status: 501,
      body: { message: 'Document conclusion flow not yet implemented' }
    };
  }
};
