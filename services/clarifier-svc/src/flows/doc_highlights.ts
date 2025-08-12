import { FlowSpec } from '../engine/flows';

export const docHighlightsFlow: FlowSpec = {
  id: 'doc_highlights',
  
  async init(_ctx: any) {
    // No dynamic initialization needed for now
    return {
      minBullets: 3,
      maxBullets: 10
    };
  },

  slots: [
    {
      key: 'bullet_count',
      type: 'int',
      prompt: (ctx: any) => `How many highlight points would you like? (${ctx.minBullets} to ${ctx.maxBullets})`,
      min: 3,
      max: 10,
      required: true,
      parserHint: 'count'
    },
    {
      key: 'include_citations',
      type: 'bool',
      prompt: (_ctx: any) => `Should the highlights include citations and references?`,
      required: true
    }
  ],

  async validate(filled: Record<string, any>, ctx: any) {
    const errors: string[] = [];

    if (typeof filled['bullet_count'] !== 'number') {
      errors.push('Bullet count must be a number');
    } else if (filled['bullet_count'] < ctx.minBullets || filled['bullet_count'] > ctx.maxBullets) {
      errors.push(`Bullet count must be between ${ctx.minBullets} and ${ctx.maxBullets}`);
    }

    if (typeof filled['include_citations'] !== 'boolean') {
      errors.push('Include citations must be true or false');
    }

    if (errors.length > 0) {
      return { ok: false, errors, filled };
    }

    return { ok: true, filled };
  },

  async finalize(_filled: Record<string, any>, _ctx: any) {
    return {
      status: 501,
      body: { message: 'Document highlights flow not yet implemented' }
    };
  }
};
