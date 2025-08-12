// Jest setup file
import { TextEncoder, TextDecoder } from 'util';

// Polyfill for TextEncoder/TextDecoder in Node.js
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any;

// Mock fetch if not available
if (!global.fetch) {
  global.fetch = jest.fn();
}

// Set test timeout
jest.setTimeout(10000);

