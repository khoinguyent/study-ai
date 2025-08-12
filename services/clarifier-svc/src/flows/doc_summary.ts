import { FlowSpec } from '../engine/flows';

export const docSummaryFlow: FlowSpec = {
  id: 'doc_summary',
  
  async init(_ctx: any) {
    // No dynamic initialization needed for now
    return {
      allowedLengths: ['short', 'medium', 'long'],
      allowedAudiences: ['k12', 'university', 'teacher'],
      allowedStyles: ['concise', 'detailed']
    };
  },

  slots: [
    {
      key: 'summary_length',
      type: 'enum',
      prompt: (ctx: any) => `How long should the summary be? Choose from: ${ctx.allowedLengths.join(', ')}`,
      ui: (ctx: any) => ({
        quick: ctx.allowedLengths
      }),
      allowed: ['short', 'medium', 'long'],
      required: true,
      parserHint: 'length'
    },
    {
      key: 'audience',
      type: 'enum',
      prompt: (ctx: any) => `Who is the target audience? Choose from: ${ctx.allowedAudiences.join(', ')}`,
      ui: (ctx: any) => ({
        quick: ctx.allowedAudiences
      }),
      allowed: ['k12', 'university', 'teacher'],
      required: true,
      parserHint: 'audience'
    },
    {
      key: 'style',
      type: 'enum',
      prompt: (ctx: any) => `What style should the summary have? Choose from: ${ctx.allowedStyles.join(', ')}`,
      ui: (ctx: any) => ({
        quick: ctx.allowedStyles
      }),
      allowed: ['concise', 'detailed'],
      required: true,
      parserHint: 'style'
    }
  ],

  async validate(filled: Record<string, any>, ctx: any) {
    const errors: string[] = [];

    if (!filled['summary_length'] || !ctx.allowedLengths.includes(filled['summary_length'])) {
      errors.push(`Summary length must be one of: ${ctx.allowedLengths.join(', ')}`);
    }

    if (!filled['audience'] || !ctx.allowedAudiences.includes(filled['audience'])) {
      errors.push(`Audience must be one of: ${ctx.allowedAudiences.join(', ')}`);
    }

    if (!filled['style'] || !ctx.allowedStyles.includes(filled['style'])) {
      errors.push(`Style must be one of: ${ctx.allowedStyles.join(', ')}`);
    }

    if (errors.length > 0) {
      return { ok: false, errors, filled };
    }

    return { ok: true, filled };
  },

  async finalize(_filled: Record<string, any>, _ctx: any) {
    return {
      status: 501,
      body: { message: 'Document summary flow not yet implemented' }
    };
  }
};
