#!/usr/bin/env python3
"""
Final comprehensive test of all EOL Scanner API endpoints
"""

import requests
import json
import sys
import time
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"
API_TOKEN = "test-token-12345"

def test_endpoint(name, method, endpoint, expected_status=200, json_data=None, headers=None, timeout=10, description=""):
    """Test a single endpoint and return results"""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if json_data is None:
        json_data = {}
    
    result = {
        "name": name,
        "method": method,
        "endpoint": endpoint,
        "expected_status": expected_status,
        "description": description,
        "success": False,
        "status_code": None,
        "response_time": None,
        "error": None,
        "details": ""
    }
    
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
        else:
            result["error"] = f"Unsupported method: {method}"
            return result
        
        result["status_code"] = response.status_code
        result["response_time"] = time.time() - start_time
        
        if response.status_code == expected_status:
            result["success"] = True
            if response.status_code == 200:
                try:
                    data = response.json()
                    if endpoint == "/health":
                        result["details"] = f"Status: {data.get('status')}, Model: {data.get('model_status')}"
                    elif endpoint == "/":
                        result["details"] = f"Version: {data.get('version')}"
                    elif endpoint == "/model/info":
                        result["details"] = f"Model type: {data.get('model_type')}, Features: {len(data.get('features', []))}"
                    elif "scan" in endpoint and "summary" in data:
                        result["details"] = f"Scan ID: {data.get('scan_id')}, Items: {data.get('summary', {}).get('total_items', 0)}"
                    elif "scans" in endpoint:
                        result["details"] = f"Found {len(data)} scans"
                    else:
                        result["details"] = "Success"
                except:
                    result["details"] = f"Response: {response.text[:100]}..."
            else:
                result["details"] = f"Expected status {expected_status}"
        else:
            result["error"] = f"Expected {expected_status}, got {response.status_code}"
            result["details"] = f"Response: {response.text[:100]}..."
            
    except requests.exceptions.Timeout:
        result["error"] = f"Timeout after {timeout}s"
    except Exception as e:
        result["error"] = str(e)
    
    return result

def main():
    """Run all endpoint tests"""
    print("🚀 EOL Scanner API - Comprehensive Endpoint Test")
    print("=" * 60)
    
    # Check if API is running
    health_check = test_endpoint("Health Check", "GET", "/health", description="Basic API health check")
    if not health_check["success"]:
        print("❌ API is not running or not responding")
        print("   Please start the API with: API_TOKEN=test-token-12345 python -m eolscan.api")
        sys.exit(1)
    
    print("✅ API is running and responding")
    print(f"   Health: {health_check['details']}")
    print()
    
    # Define all tests
    tests = [
        # Public endpoints
        ("Root Endpoint", "GET", "/", 200, None, None, 10, "API root information"),
        ("Health Check", "GET", "/health", 200, None, None, 10, "System health status"),
        ("Model Info", "GET", "/model/info", 200, None, None, 10, "Risk model information"),
        ("API Docs", "GET", "/docs", 200, None, None, 10, "OpenAPI documentation"),
        ("ReDoc", "GET", "/redoc", 200, None, None, 10, "ReDoc documentation"),
        
        # Authentication tests
        ("Auth Required (no token)", "GET", "/scan", 401, None, None, 10, "Should require authentication"),
        ("Auth Required (invalid token)", "GET", "/scan", 401, None, 
         {"Authorization": "Bearer invalid-token"}, 10, "Should reject invalid token"),
        
        # Authenticated endpoints
        ("List Scans", "GET", "/scans?limit=5", 200, None, 
         {"Authorization": f"Bearer {API_TOKEN}"}, 10, "List recent scans"),
        
        # Scan endpoints
        ("Local Path Scan", "POST", "/scan", 200,
         {"path": ".", "near_months": 6, "include_risk_assessment": False},
         {"Authorization": f"Bearer {API_TOKEN}"}, 30, "Scan local directory"),
        
        ("Repository Scan", "POST", "/scan", 200,
         {"repo": "microsoft/vscode", "near_months": 6, "include_risk_assessment": False},
         {"Authorization": f"Bearer {API_TOKEN}"}, 60, "Scan GitHub repository"),
        
        ("Batch Scan", "POST", "/scan/batch", 200,
         [{"path": ".", "include_risk_assessment": False}],
         {"Authorization": f"Bearer {API_TOKEN}"}, 60, "Batch scan multiple targets"),
        
        ("Model Training", "POST", "/model/train", 200,
         [{"name": "test", "version": "1.0", "type": "package", "status": "EOL", "risk_level": "HIGH"}],
         {"Authorization": f"Bearer {API_TOKEN}"}, 30, "Train risk model"),
        
        # Error handling tests
        ("Invalid Request", "POST", "/scan", 400,
         {"invalid_field": "test"},
         {"Authorization": f"Bearer {API_TOKEN}"}, 10, "Handle invalid requests"),
        
        ("Not Found", "GET", "/scan/nonexistent-id", 404, None,
         {"Authorization": f"Bearer {API_TOKEN}"}, 10, "Handle non-existent resources"),
    ]
    
    # Run all tests
    results = []
    for test in tests:
        print(f"Testing: {test[0]}...")
        result = test_endpoint(*test)
        results.append(result)
        
        if result["success"]:
            print(f"  ✅ {result['details']}")
        else:
            print(f"  ❌ {result['error']}")
        
        time.sleep(0.5)  # Small delay between tests
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Group results by category
    categories = {
        "Public Endpoints": [],
        "Authentication": [],
        "Core Functionality": [],
        "Error Handling": []
    }
    
    for result in results:
        if result["endpoint"] in ["/", "/health", "/model/info", "/docs", "/redoc"]:
            categories["Public Endpoints"].append(result)
        elif "auth" in result["name"].lower() or result["expected_status"] == 401:
            categories["Authentication"].append(result)
        elif "error" in result["name"].lower() or result["expected_status"] in [400, 404]:
            categories["Error Handling"].append(result)
        else:
            categories["Core Functionality"].append(result)
    
    # Print detailed results by category
    for category, category_results in categories.items():
        if category_results:
            print(f"\n{category}:")
            category_passed = sum(1 for r in category_results if r["success"])
            print(f"  {category_passed}/{len(category_results)} passed")
            
            for result in category_results:
                status = "✅" if result["success"] else "❌"
                print(f"    {status} {result['name']}: {result['details'] or result['error']}")
    
    # Show scan IDs if any scans were successful
    scan_results = [r for r in results if "scan" in r["endpoint"] and r["success"]]
    if scan_results:
        print(f"\n📋 Successful Scans: {len(scan_results)}")
    
    # Final verdict
    print("\n" + "=" * 60)
    if passed == total:
        print("🎉 ALL TESTS PASSED! API is working correctly.")
        return True
    elif passed >= total * 0.8:
        print("✅ MOST TESTS PASSED! API is working well with minor issues.")
        return True
    elif passed >= total * 0.6:
        print("⚠️ MANY TESTS PASSED! API has some issues but core functionality works.")
        return True
    else:
        print("❌ MANY TESTS FAILED! API has significant issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
