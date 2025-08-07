#!/usr/bin/env python3

import requests
import json

# Test document service directly
BASE_URL = "http://localhost:8002"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code}")
    print(response.json())

def test_subject_creation():
    """Test subject creation"""
    data = {
        "name": "History",
        "description": "Historical events and periods"
    }
    
    response = requests.post(
        f"{BASE_URL}/subjects",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Subject creation: {response.status_code}")
    print(response.text)

if __name__ == "__main__":
    print("Testing document service directly...")
    test_health()
    print("\n" + "="*50 + "\n")
    test_subject_creation() 