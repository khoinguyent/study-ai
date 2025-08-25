import OpenAI from 'openai';
import { LRUCache } from 'lru-cache';
import { createHash } from 'crypto';
import { EmbeddingResult } from '../../types';
import logger from '../logger';
import config from '../config';

export class OpenAIEmbeddingsClient {
  private client: OpenAI;
  private cache: LRUCache<string, number[]>;
  private batchSize: number;
  private maxSpans: number;

  constructor() {
    if (!config.OPENAI_API_KEY) {
      throw new Error('OPENAI_API_KEY is required for embeddings');
    }

    this.client = new OpenAI({
      apiKey: config.OPENAI_API_KEY,
    });

    this.batchSize = config.QB_EMBEDDINGS_BATCH_SIZE;
    this.maxSpans = config.QB_MAX_SPANS_FOR_EMBEDDINGS;

    // Initialize cache with TTL
    this.cache = new LRUCache<string, number[]>({
      max: 1000, // Maximum number of items
      ttl: config.QB_EMBEDDINGS_CACHE_TTL_SEC * 1000, // Convert to milliseconds
    });
  }

  /**
   * Generate embeddings for a batch of texts
   */
  async embed(texts: string[], options?: { batchSize?: number }): Promise<EmbeddingResult> {
    const batchSize = options?.batchSize || this.batchSize;
    
    if (texts.length > this.maxSpans) {
      logger.warn(`Text count ${texts.length} exceeds maxSpans ${this.maxSpans}, falling back to heuristic dedupe`);
      throw new Error(`Text count ${texts.length} exceeds maximum allowed ${this.maxSpans}`);
    }

    const allVectors: number[][] = [];
    let totalPromptTokens = 0;
    let totalTokens = 0;

    // Process in batches
    for (let i = 0; i < texts.length; i += batchSize) {
      const batch = texts.slice(i, i + batchSize);
      const batchVectors = await this.processBatch(batch);
      
      allVectors.push(...batchVectors.vectors);
      totalPromptTokens += batchVectors.usage.prompt_tokens;
      totalTokens += batchVectors.usage.total_tokens;
    }

    return {
      vectors: allVectors,
      usage: {
        prompt_tokens: totalPromptTokens,
        total_tokens: totalTokens,
      },
    };
  }

  /**
   * Process a single batch of texts
   */
  private async processBatch(texts: string[]): Promise<EmbeddingResult> {
    try {
      const response = await this.client.embeddings.create({
        model: config.QB_EMBEDDINGS_MODEL,
        input: texts,
        encoding_format: 'float',
      });

      const vectors = response.data.map(item => item.embedding);
      
      // Cache individual embeddings
      texts.forEach((text, index) => {
        const hash = this.generateTextHash(text);
        this.cache.set(hash, vectors[index]);
      });

      return {
        vectors,
        usage: {
          prompt_tokens: response.usage?.prompt_tokens || 0,
          total_tokens: response.usage?.total_tokens || 0,
        },
      };
    } catch (error) {
      logger.error('Error generating embeddings:', error);
      throw new Error(`Failed to generate embeddings: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get cached embedding if available
   */
  getCachedEmbedding(text: string): number[] | undefined {
    const hash = this.generateTextHash(text);
    return this.cache.get(hash);
  }

  /**
   * Generate hash for text to use as cache key
   */
  private generateTextHash(text: string): string {
    return createHash('sha256').update(text).digest('hex');
  }

  /**
   * Check if embeddings are enabled and API key is available
   */
  isAvailable(): boolean {
    return config.QB_EMBEDDINGS_ENABLED && !!config.OPENAI_API_KEY;
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      size: this.cache.size,
      max: this.cache.max,
      ttl: config.QB_EMBEDDINGS_CACHE_TTL_SEC,
    };
  }
}
