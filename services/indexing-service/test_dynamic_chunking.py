#!/usr/bin/env python3
"""
Test script for dynamic chunking functionality
"""
import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, '/app')

from app.services.chunking.dynamic_chunker import chunk_section_dynamic
from app.services.chunking.sectionizer import Section
from app.config import Settings

async def test_dynamic_chunking():
    """Test dynamic chunking with a sample document"""
    
    # Sample document with mixed content (prose, lists, code, math)
    test_text = """
# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions without being explicitly programmed. This field has seen tremendous growth in recent years, with applications ranging from image recognition to natural language processing.

## Key Concepts

1. **Supervised Learning**: Training with labeled data to predict outcomes
2. **Unsupervised Learning**: Finding patterns in unlabeled data  
3. **Reinforcement Learning**: Learning through trial and error and rewards

## Mathematical Foundation

The basic equation for linear regression is: y = mx + b

Where:
- y is the dependent variable
- m is the slope coefficient  
- x is the independent variable
- b is the y-intercept

## Code Example

```python
import numpy as np
from sklearn.linear_model import LinearRegression

# Create sample data
X = np.array([[1], [2], [3], [4], [5]])
y = np.array([2, 4, 6, 8, 10])

# Train model
model = LinearRegression()
model.fit(X, y)
print(f"Slope: {model.coef_[0]:.2f}")
print(f"Intercept: {model.intercept_:.2f}")
```

This demonstrates the power of machine learning algorithms in practice.
"""
    
    # Create a section
    section = Section(
        headingPath=["Machine Learning", "Introduction"],
        text=test_text,
        pageStart=1,
        pageEnd=1,
        type="normal"
    )
    
    # Create config with dynamic chunking settings
    config = Settings(
        CHUNK_MODE="DYNAMIC",
        CHUNK_BASE_TOKENS=320,
        CHUNK_MIN_TOKENS=180,
        CHUNK_MAX_TOKENS=480,
        CHUNK_SENT_OVERLAP_RATIO=0.12,
        LABSE_MAX_TOKENS=512,
        DENSITY_WEIGHT_SYMBOLS=0.4,
        DENSITY_WEIGHT_AVGWORD=0.3,
        DENSITY_WEIGHT_NUMBERS=0.3
    )
    
    print("Testing Dynamic Chunking...")
    print("=" * 50)
    print(f"Original text length: {len(test_text)} characters")
    print(f"Config: CHUNK_MODE={config.CHUNK_MODE}")
    print(f"Target tokens: {config.CHUNK_BASE_TOKENS} (min: {config.CHUNK_MIN_TOKENS}, max: {config.CHUNK_MAX_TOKENS})")
    print(f"LaBSE max tokens: {config.LABSE_MAX_TOKENS}")
    print()
    
    # Test dynamic chunking
    chunks = await chunk_section_dynamic(section, config)
    
    print(f"Created {len(chunks)} chunks:")
    print("=" * 50)
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"Text preview: {chunk.text[:100]}...")
        print(f"Tokens: {chunk.tokens}")
        print(f"Type: {chunk.meta.get('type', 'unknown')}")
        print(f"Heading: {chunk.meta.get('heading_path', [])}")
        print(f"Page range: {chunk.meta.get('page_start')}-{chunk.meta.get('page_end')}")
        print("-" * 30)
    
    # Validate chunk constraints
    print("\nValidation:")
    print("=" * 50)
    
    all_valid = True
    for i, chunk in enumerate(chunks):
        if chunk.tokens > config.LABSE_MAX_TOKENS - 32:
            print(f"❌ Chunk {i+1} exceeds LaBSE limit: {chunk.tokens} > {config.LABSE_MAX_TOKENS - 32}")
            all_valid = False
        elif chunk.tokens < config.CHUNK_MIN_TOKENS:
            print(f"⚠️  Chunk {i+1} below minimum: {chunk.tokens} < {config.CHUNK_MIN_TOKENS}")
        elif chunk.tokens > config.CHUNK_MAX_TOKENS:
            print(f"⚠️  Chunk {i+1} above maximum: {chunk.tokens} > {config.CHUNK_MAX_TOKENS}")
        else:
            print(f"✅ Chunk {i+1} within bounds: {chunk.tokens} tokens")
    
    if all_valid:
        print("\n🎉 All chunks respect LaBSE token limits!")
    else:
        print("\n❌ Some chunks violate constraints")
    
    return chunks

if __name__ == "__main__":
    try:
        chunks = asyncio.run(test_dynamic_chunking())
        print(f"\n✅ Dynamic chunking test completed successfully!")
        print(f"📊 Total chunks created: {len(chunks)}")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
