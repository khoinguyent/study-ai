#!/usr/bin/env node

/**
 * Example usage of the enhanced Question Budget Service
 * This demonstrates both the legacy and new enhanced endpoints
 */

const BASE_URL = 'http://localhost:8011';

// Example request for the new enhanced /estimate endpoint
const enhancedRequest = {
  subjectId: "vietnam-history-101",
  totalTokens: 50000,
  distinctSpanCount: 150, // Optional - service will estimate if not provided
  mix: {
    mcq: 10,
    short: 5,
    truefalse: 3,
    fill_blank: 2
  },
  difficulty: "medium",
  costBudgetUSD: 10.0,
  modelPricing: {
    inputPerMTokUSD: 0.0015,  // GPT-4 pricing example
    outputPerMTokUSD: 0.006
  },
  batching: {
    questionsPerCall: 30,
    fileSearchToolCostPer1kCallsUSD: 2.5
  },
  config: {
    // Optional configuration overrides
    embeddingsEnabled: true,
    similarityThreshold: 0.88,
    maxSpansForEmbeddings: 5000,
    spanTokenTarget: 300,
    minTokensPerQuestion: 600,
    minQuestions: 5,
    hardCap: 200
  }
};

// Example request for the legacy /budget endpoint
const legacyRequest = {
  docIds: ["doc1", "doc2", "doc3"],
  difficulty: "mixed"
};

async function testEnhancedEndpoint() {
  console.log('🧮 Testing Enhanced Budget Endpoint (/estimate)');
  console.log('=' .repeat(50));
  
  try {
    const response = await fetch(`${BASE_URL}/estimate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(enhancedRequest)
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('✅ Enhanced budget calculation successful!');
      console.log(`📊 Maximum Questions: ${result.qMax}`);
      console.log(`💰 Cost per Question: $${result.perQuestionCostUSD.toFixed(6)}`);
      console.log('\n📋 Breakdown:');
      console.log(`   Evidence Cap: ${result.qEvidence}`);
      console.log(`   Cost Cap: ${result.qCost}`);
      console.log(`   Policy Cap: ${result.qPolicy}`);
      console.log(`   Length Guard: ${result.qLengthGuard}`);
      console.log('\n📝 Notes:');
      result.notes.forEach(note => console.log(`   • ${note}`));
    } else {
      const error = await response.text();
      console.log('❌ Enhanced budget calculation failed:', error);
    }
  } catch (error) {
    console.log('❌ Error calling enhanced endpoint:', error.message);
  }
}

async function testLegacyEndpoint() {
  console.log('\n🔄 Testing Legacy Budget Endpoint (/budget)');
  console.log('=' .repeat(50));
  
  try {
    const response = await fetch(`${BASE_URL}/budget`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(legacyRequest)
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('✅ Legacy budget calculation successful!');
      console.log(`📊 Maximum Questions: ${result.maxQuestions}`);
      console.log('\n📋 Rationale:');
      console.log(`   Total Tokens: ${result.rationale.totalTokens}`);
      console.log(`   Tokens per Question: ${result.rationale.tpq}`);
      console.log(`   Coverage Cap: ${result.rationale.coverageCap}`);
      console.log(`   Concept Cap: ${result.rationale.conceptCap}`);
    } else {
      const error = await response.text();
      console.log('❌ Legacy budget calculation failed:', error);
    }
  } catch (error) {
    console.log('❌ Error calling legacy endpoint:', error.message);
  }
}

async function testStatusEndpoint() {
  console.log('\n📊 Testing Status Endpoint (/status)');
  console.log('=' .repeat(50));
  
  try {
    const response = await fetch(`${BASE_URL}/status`);
    
    if (response.ok) {
      const result = await response.json();
      console.log('✅ Status endpoint successful!');
      console.log(`🏗️  Environment: ${result.environment}`);
      console.log(`🧠 Embeddings: ${result.embeddings.enabled ? 'Enabled' : 'Disabled'}`);
      if (result.embeddings.enabled) {
        console.log(`   Model: ${result.embeddings.model}`);
        console.log(`   Batch Size: ${result.embeddings.batchSize}`);
        console.log(`   Max Spans: ${result.embeddings.maxSpans}`);
        console.log(`   Similarity Threshold: ${result.embeddings.similarityThreshold}`);
      }
      console.log(`📊 Budget Config:`);
      console.log(`   Min Questions: ${result.budget.minQuestions}`);
      console.log(`   Hard Cap: ${result.budget.hardCap}`);
      console.log(`   Span Tokens: ${result.budget.spanTokens}`);
    } else {
      const error = await response.text();
      console.log('❌ Status endpoint failed:', error);
    }
  } catch (error) {
    console.log('❌ Error calling status endpoint:', error.message);
  }
}

async function main() {
  console.log('🚀 Question Budget Service - Example Usage');
  console.log('=' .repeat(60));
  
  // Test all endpoints
  await testEnhancedEndpoint();
  await testLegacyEndpoint();
  await testStatusEndpoint();
  
  console.log('\n🎯 Example completed!');
  console.log('\n💡 To use this service:');
  console.log('   1. Set OPENAI_API_KEY for embeddings (optional)');
  console.log('   2. Configure budget parameters via environment variables');
  console.log('   3. Call /estimate for enhanced budget calculation');
  console.log('   4. Call /budget for legacy compatibility');
}

// Run the example
if (require.main === module) {
  main().catch(console.error);
}

module.exports = {
  enhancedRequest,
  legacyRequest,
  testEnhancedEndpoint,
  testLegacyEndpoint,
  testStatusEndpoint
};
