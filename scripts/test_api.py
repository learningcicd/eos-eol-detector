#!/usr/bin/env python3
"""
Test script for EOL Scanner API
"""

import requests
import json
import sys
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
API_TOKEN = "test-token"  # Change this to your actual token

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Model status: {data['model_status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_model_info():
    """Test model info endpoint"""
    print("\n🤖 Testing model info endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/model/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Model info: {data['model_type']}")
            print(f"   Features: {len(data['features'])}")
            return True
        else:
            print(f"❌ Model info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Model info error: {e}")
        return False

def test_scan_repo():
    """Test repository scanning"""
    print("\n📦 Testing repository scan...")
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "repo": "microsoft/vscode",
        "near_months": 6,
        "include_risk_assessment": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/scan",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Repository scan completed")
            print(f"   Scan ID: {data['scan_id']}")
            print(f"   Total items: {data['summary']['total_items']}")
            print(f"   EOL count: {data['summary']['eol_count']}")
            print(f"   Critical risks: {data['summary']['critical_risks']}")
            return True
        else:
            print(f"❌ Repository scan failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Repository scan error: {e}")
        return False

def test_scan_path():
    """Test local path scanning"""
    print("\n📁 Testing local path scan...")
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "path": ".",
        "near_months": 6,
        "include_risk_assessment": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/scan",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Local path scan completed")
            print(f"   Scan ID: {data['scan_id']}")
            print(f"   Total items: {data['summary']['total_items']}")
            return True
        else:
            print(f"❌ Local path scan failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Local path scan error: {e}")
        return False

def test_batch_scan():
    """Test batch scanning"""
    print("\n🔄 Testing batch scan...")
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = [
        {"repo": "microsoft/vscode"},
        {"repo": "facebook/react"},
        {"path": "."}
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/scan/batch",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Batch scan completed")
            print(f"   Batch ID: {data['batch_id']}")
            print(f"   Total requests: {data['total_requests']}")
            print(f"   Successful: {data['successful']}")
            print(f"   Failed: {data['failed']}")
            return True
        else:
            print(f"❌ Batch scan failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Batch scan error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting EOL Scanner API Tests")
    print("=" * 50)
    
    # Check if API is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print("❌ API is not running. Please start the API first:")
        print("   python -m eolscan.api")
        sys.exit(1)
    
    tests = [
        test_health,
        test_model_info,
        test_scan_repo,
        test_scan_path,
        test_batch_scan
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Small delay between tests
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
