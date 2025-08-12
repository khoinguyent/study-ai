declare module 'fastify-cors' {
  import { FastifyPluginCallback } from 'fastify';

  interface FastifyCorsOptions {
    origin?: boolean | string | string[] | RegExp | RegExp[] | ((origin: string, cb: (err: Error | null, allow?: boolean) => void) => void);
    methods?: string | string[];
    allowedHeaders?: string | string[];
    exposedHeaders?: string | string[];
    credentials?: boolean;
    maxAge?: number;
    preflight?: boolean;
    preflightContinue?: boolean;
    optionsSuccessStatus?: number;
    strictPreflight?: boolean;
    hideOptionsRoute?: boolean;
  }

  const fastifyCors: FastifyPluginCallback<FastifyCorsOptions>;
  export = fastifyCors;
}

