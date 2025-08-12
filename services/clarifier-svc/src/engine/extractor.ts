import env from '../lib/env';
import logger from '../lib/logger';

export interface ExtractorResult {
  [key: string]: any;
  out_of_scope?: boolean;
}

export class LLMExtractor {
  private enabled: boolean;
  private url: string | undefined;

  constructor() {
    this.enabled = env.USE_LLM_EXTRACTOR === 'true';
    this.url = env.EXTRACTOR_URL || undefined;
    
    if (this.enabled && !this.url) {
      logger.warn('USE_LLM_EXTRACTOR is enabled but EXTRACTOR_URL is not set');
      this.enabled = false;
    }
  }

  async extract(text: string, _currentSlot: string, parserHint?: string): Promise<ExtractorResult> {
    if (!this.enabled || !this.url) {
      return {};
    }

    try {
      const systemPrompt = this.buildSystemPrompt(_currentSlot, parserHint);
      
      const response = await fetch(this.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          system_prompt: systemPrompt,
          user_input: text,
          max_tokens: 200
        })
      });

      if (!response.ok) {
        logger.error(`LLM extractor failed: ${response.status} ${response.statusText}`);
        return {};
      }

      const result = await response.json();
      
      // Validate and clean the result
      const cleaned = this.cleanExtractionResult(result, _currentSlot);
      logger.info(`LLM extractor result for slot ${_currentSlot}:`, cleaned);
      
      return cleaned;
    } catch (error) {
      logger.error('LLM extractor error:', error);
      return {};
    }
  }

  private buildSystemPrompt(_currentSlot: string, parserHint?: string): string {
    let prompt = `You are a JSON extractor for a quiz setup system. Extract ONLY the requested information and return valid JSON.`;

    switch (_currentSlot) {
      case 'question_types':
        prompt += `\n\nExtract question types from the text. Allowed values: ["mcq", "true_false", "fill_blank", "short_answer"].
Return: {"question_types": ["type1", "type2"]} or {} if none found.`;
        break;
        
      case 'difficulty':
        prompt += `\n\nExtract difficulty level from the text. Allowed values: ["easy", "medium", "hard", "mixed"].
Return: {"difficulty": "level"} or {} if none found.`;
        break;
        
      case 'requested_count':
        prompt += `\n\nExtract the number of questions requested. Return: {"requested_count": number} or {} if none found.`;
        break;
        
      default:
        if (parserHint === 'qtype') {
          prompt += `\n\nExtract question types. Allowed: ["mcq", "true_false", "fill_blank", "short_answer"].
Return: {"question_types": ["type1", "type2"]} or {} if none found.`;
        } else if (parserHint === 'difficulty') {
          prompt += `\n\nExtract difficulty level. Allowed: ["easy", "medium", "hard", "mixed"].
Return: {"difficulty": "level"} or {} if none found.`;
        } else if (parserHint === 'count') {
          prompt += `\n\nExtract a numeric count. Return: {"count": number} or {} if none found.`;
        } else {
          prompt += `\n\nExtract relevant information for slot "${_currentSlot}". Return valid JSON or {}.`;
        }
    }

    prompt += `\n\nIMPORTANT: Return ONLY valid JSON. No explanations or additional text.`;
    
    return prompt;
  }

  private cleanExtractionResult(result: any, _currentSlot: string): ExtractorResult {
    try {
      // Handle different response formats
      let jsonData: any = {};
      
      if (typeof result === 'string') {
        // Try to extract JSON from string response
        const jsonMatch = result.match(/\{.*\}/s);
        if (jsonMatch) {
          jsonData = JSON.parse(jsonMatch[0]);
        }
      } else if (result.content) {
        // Handle OpenAI-style responses
        const jsonMatch = result.content.match(/\{.*\}/s);
        if (jsonMatch) {
          jsonData = JSON.parse(jsonMatch[0]);
        }
      } else if (result.choices && result.choices[0]?.message?.content) {
        // Handle OpenAI API response
        const jsonMatch = result.choices[0].message.content.match(/\{.*\}/s);
        if (jsonMatch) {
          jsonData = JSON.parse(jsonMatch[0]);
        }
      } else if (typeof result === 'object') {
        jsonData = result;
      }

      // Validate the extracted data
      const cleaned: ExtractorResult = {};
      
      if (jsonData['question_types'] && Array.isArray(jsonData['question_types'])) {
        cleaned['question_types'] = jsonData['question_types'];
      }
      
      if (jsonData['difficulty'] && typeof jsonData['difficulty'] === 'string') {
        cleaned['difficulty'] = jsonData['difficulty'];
      }
      
      if (jsonData['requested_count'] && typeof jsonData['requested_count'] === 'number') {
        cleaned['requested_count'] = jsonData['requested_count'];
      }
      
      if (jsonData['count'] && typeof jsonData['count'] === 'number') {
        cleaned['count'] = jsonData['count'];
      }
      
      if (jsonData['out_of_scope'] === true) {
        cleaned['out_of_scope'] = true;
      }

      return cleaned;
    } catch (error) {
      logger.error('Failed to clean extraction result:', error);
      return {};
    }
  }

  isEnabled(): boolean {
    return this.enabled;
  }
}

export const llmExtractor = new LLMExtractor();
