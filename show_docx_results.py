#!/usr/bin/env python3
"""
Quick summary script to show DOCX parsing and chunking results
"""

import json
from pathlib import Path
import glob

def show_latest_analysis():
    """Show the latest DOCX analysis results"""
    # Find the latest analysis file
    analysis_files = glob.glob("docx_analysis_*.json")
    if not analysis_files:
        print("❌ No analysis files found. Run the analyzer first.")
        return
    
    # Get the latest file
    latest_file = max(analysis_files, key=Path.stat)
    print(f"📊 Latest Analysis: {latest_file}")
    print("=" * 50)
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data.get('success'):
            print("✅ DOCX Analysis Results")
            print("-" * 30)
            print(f"📄 Format: {data['format'].upper()}")
            print(f"📝 Words: {data['word_count']:,}")
            print(f"🔤 Characters: {data['character_count']:,}")
            print(f"🔧 Method: {data['extraction_method']}")
            
            # Structure info
            structure = data.get('structure', {})
            if 'paragraphs' in structure:
                print(f"📄 Paragraphs: {structure['paragraphs']}")
            if 'tables' in structure:
                print(f"📊 Tables: {structure['tables']}")
            if 'sections' in structure:
                print(f"📑 Sections: {structure['sections']}")
            
            print()
            
            # Text preview
            text = data.get('text', '')
            if text:
                print("📖 Text Preview (first 300 chars):")
                print("-" * 40)
                preview = text[:300]
                if len(text) > 300:
                    preview += "..."
                print(preview)
                print("-" * 40)
                print()
            
            # Chunking analysis
            print("✂️  Chunking Analysis")
            print("-" * 25)
            
            # Test different strategies
            from advanced_document_analyzer import DocumentAnalyzer
            analyzer = DocumentAnalyzer()
            
            strategies = ['paragraph', 'sentence', 'fixed']
            best_strategy = None
            best_chunks = 0
            
            for strategy in strategies:
                chunks = analyzer.chunk_text_advanced(text, max_chunk_size=1000, strategy=strategy)
                analysis = analyzer.analyze_chunks(chunks)
                
                print(f"  {strategy.capitalize()}:")
                print(f"    Chunks: {analysis['total_chunks']}")
                print(f"    Avg size: {analysis['average_chunk_size']:.1f} chars")
                print(f"    Range: {analysis['smallest_chunk']} - {analysis['largest_chunk']} chars")
                
                # Track best strategy (most chunks with good size distribution)
                dist = analysis['size_distribution']
                good_chunks = dist['500_1000']  # Chunks in optimal range
                if good_chunks > best_chunks:
                    best_chunks = good_chunks
                    best_strategy = strategy
            
            print()
            print(f"🏆 Best Strategy: {best_strategy} (most chunks in optimal size range)")
            
            # Show sample chunks from best strategy
            if best_strategy:
                print(f"\n📋 Sample chunks from {best_strategy} strategy:")
                print("-" * 45)
                
                chunks = analyzer.chunk_text_advanced(text, max_chunk_size=1000, strategy=best_strategy)
                for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                    print(f"Chunk {i+1} ({chunk['size']} chars):")
                    content = chunk['content'][:100]
                    if len(chunk['content']) > 100:
                        content += "..."
                    print(f"  {content}")
                    print()
                
                if len(chunks) > 3:
                    print(f"... and {len(chunks) - 3} more chunks")
            
        else:
            print(f"❌ Analysis failed: {data.get('error')}")
    
    except Exception as e:
        print(f"❌ Error reading analysis file: {e}")

def show_file_info():
    """Show information about the DOCX file"""
    docx_path = Path("data/Đồng Bằng Sông Cửu Long.docx")
    
    if docx_path.exists():
        print("📄 DOCX File Information")
        print("=" * 30)
        print(f"📁 Path: {docx_path}")
        print(f"📊 Size: {docx_path.stat().st_size / 1024:.1f} KB")
        print(f"📅 Modified: {datetime.fromtimestamp(docx_path.stat().st_mtime)}")
        print()
    else:
        print("❌ DOCX file not found")

if __name__ == "__main__":
    from datetime import datetime
    
    print("🚀 DOCX Parsing and Chunking Results Summary")
    print("=" * 60)
    print()
    
    show_file_info()
    show_latest_analysis()
    
    print("\n🎉 Summary completed!")
