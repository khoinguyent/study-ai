#!/usr/bin/env python3
"""
PDF Parser Debug Tool

Usage:
    python parse_pdf_debug.py <local_file_path>
    python parse_pdf_debug.py --s3 s3://bucket/key
    python parse_pdf_debug.py --url https://example.com/file.pdf

This tool helps debug PDF parsing issues by showing detailed extraction results.
"""

import argparse
import sys
import os
import boto3
import requests
from pathlib import Path

# Add the indexing service parsers to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'indexing-service', 'src'))

try:
    from parsers.pdf_extractor import extract_pdf, get_pdf_info
    PARSER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PDF parser not available: {e}")
    PARSER_AVAILABLE = False

def download_from_s3(s3_url: str) -> bytes:
    """Download file from S3 URL"""
    try:
        # Parse S3 URL: s3://bucket/key
        if not s3_url.startswith('s3://'):
            raise ValueError("S3 URL must start with s3://")
        
        parts = s3_url[5:].split('/', 1)
        if len(parts) != 2:
            raise ValueError("Invalid S3 URL format: s3://bucket/key")
        
        bucket, key = parts
        
        # Use boto3 to download
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
        
    except Exception as e:
        print(f"Error downloading from S3: {e}")
        sys.exit(1)

def download_from_url(url: str) -> bytes:
    """Download file from HTTP URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
        
    except Exception as e:
        print(f"Error downloading from URL: {e}")
        sys.exit(1)

def analyze_pdf(content: bytes, filename: str = "unknown.pdf"):
    """Analyze PDF content and show detailed results"""
    if not PARSER_AVAILABLE:
        print("PDF parser not available. Install required dependencies.")
        return
    
    print(f"\n{'='*60}")
    print(f"PDF Analysis: {filename}")
    print(f"{'='*60}")
    
    # Basic info
    print(f"File size: {len(content):,} bytes")
    
    # Get basic PDF info
    print("\n--- Basic PDF Info ---")
    info = get_pdf_info(content)
    if info['success']:
        print(f"Page count: {info['page_count']}")
        if 'metadata' in info and info['metadata']:
            meta = info['metadata']
            if meta.get('title'):
                print(f"Title: {meta['title']}")
            if meta.get('author'):
                print(f"Author: {meta['author']}")
            if meta.get('creator'):
                print(f"Creator: {meta['creator']}")
    else:
        print(f"Error getting PDF info: {info.get('error', 'Unknown')}")
        return
    
    # Extract text
    print("\n--- Text Extraction ---")
    result = extract_pdf(content)
    
    if result['success']:
        print(f"Extraction method: {result['extraction_method']}")
        print(f"OCR used: {result['ocr_used']}")
        print(f"Total characters: {result['statistics']['total_characters']:,}")
        print(f"Total words: {result['statistics']['total_words']:,}")
        print(f"Pages with content: {result['statistics']['pages_with_content']}")
        print(f"Average chars per page: {result['statistics']['average_chars_per_page']:.1f}")
        
        # Show per-page details
        print("\n--- Per-Page Details ---")
        for page in result['pages']:
            print(f"Page {page['page']}: {page['char_count']:,} chars, {page['word_count']:,} words, method: {page['method']}")
        
        # Show text preview
        print(f"\n--- Text Preview (first 500 chars) ---")
        preview = result['full_text'][:500]
        if len(result['full_text']) > 500:
            preview += "..."
        print(preview)
        
        # Show text quality assessment
        if 'text_quality' in result['metadata']:
            quality = result['metadata']['text_quality']
            print(f"\n--- Text Quality ---")
            print(f"Score: {quality['score']}/100")
            print(f"Quality: {quality['quality']}")
            if quality.get('issues'):
                print("Issues found:")
                for issue in quality['issues']:
                    print(f"  - {issue}")
        
    else:
        print(f"Text extraction failed: {result.get('error', 'Unknown error')}")

def main():
    parser = argparse.ArgumentParser(description="Debug PDF parsing issues")
    parser.add_argument("file_path", nargs="?", help="Local PDF file path")
    parser.add_argument("--s3", help="S3 URL (s3://bucket/key)")
    parser.add_argument("--url", help="HTTP URL to PDF file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if not args.file_path and not args.s3 and not args.url:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.s3:
            print(f"Downloading from S3: {args.s3}")
            content = download_from_s3(args.s3)
            filename = args.s3.split('/')[-1]
        elif args.url:
            print(f"Downloading from URL: {args.url}")
            content = download_from_url(args.url)
            filename = args.url.split('/')[-1]
        else:
            # Local file
            file_path = Path(args.file_path)
            if not file_path.exists():
                print(f"File not found: {file_path}")
                sys.exit(1)
            
            print(f"Reading local file: {file_path}")
            with open(file_path, 'rb') as f:
                content = f.read()
            filename = file_path.name
        
        analyze_pdf(content, filename)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
