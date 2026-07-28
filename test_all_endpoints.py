"""
Comprehensive Endpoint Verification Script
Tests all Academy Sports API endpoints to ensure frontend-backend consistency
"""

import requests
import json
from typing import Dict, List

API_BASE_URL = "http://localhost:8002"

class EndpointTester:
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def test_get(self, endpoint: str, description: str):
        """Test a GET endpoint"""
        try:
            url = f"{API_BASE_URL}{endpoint}"
            print(f"\n[TEST] GET {endpoint}")
            print(f"   Description: {description}")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"   [PASS] SUCCESS - Status: {response.status_code}")
                self.passed.append(endpoint)
                return True
            elif response.status_code == 404:
                print(f"   [WARN] NOT FOUND - Status: {response.status_code}")
                print(f"   Message: {response.text[:200]}")
                self.failed.append(f"{endpoint} (404 - Expected if no data loaded)")
                return False
            else:
                print(f"   [FAIL] FAILED - Status: {response.status_code}")
                print(f"   Message: {response.text[:200]}")
                self.failed.append(f"{endpoint} ({response.status_code})")
                return False
        except Exception as e:
            print(f"   [ERROR] {str(e)}")
            self.failed.append(f"{endpoint} (Exception: {str(e)})")
            return False
    
    def test_post(self, endpoint: str, description: str, data: Dict = None):
        """Test a POST endpoint"""
        try:
            url = f"{API_BASE_URL}{endpoint}"
            print(f"\n[TEST] POST {endpoint}")
            print(f"   Description: {description}")
            response = requests.post(url, json=data or {}, timeout=30)
            
            if response.status_code in [200, 201]:
                print(f"   [PASS] SUCCESS - Status: {response.status_code}")
                self.passed.append(endpoint)
                return True
            else:
                print(f"   [FAIL] FAILED - Status: {response.status_code}")
                print(f"   Message: {response.text[:200]}")
                self.failed.append(f"{endpoint} ({response.status_code})")
                return False
        except Exception as e:
            print(f"   [ERROR] {str(e)}")
            self.failed.append(f"{endpoint} (Exception: {str(e)})")
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"\n[PASS] Passed: {len(self.passed)}/{len(self.passed) + len(self.failed)}")
        for ep in self.passed:
            print(f"   + {ep}")
        
        if self.failed:
            print(f"\n[FAIL] Failed: {len(self.failed)}/{len(self.passed) + len(self.failed)}")
            for ep in self.failed:
                print(f"   - {ep}")
        
        print("\n" + "="*80)

def main():
    print("="*80)
    print("ACADEMY SPORTS API ENDPOINT VERIFICATION")
    print("="*80)
    print(f"API Base URL: {API_BASE_URL}")
    
    tester = EndpointTester()
    
    # ========================================
    # AGENT A ENDPOINTS (Used in AcademyAgentA.tsx)
    # ========================================
    print("\n\n" + "="*80)
    print("AGENT A ENDPOINTS")
    print("="*80)
    
    tester.test_get(
        "/api/academy/agent_a/results",
        "Get Agent A clustering results"
    )
    
    tester.test_post(
        "/api/academy/agent_a/execute",
        "Execute Agent A clustering",
        {"n_clusters": 3, "gamma": 0.5}
    )
    
    tester.test_get(
        "/api/academy/agent_a/export",
        "Export Agent A results to CSV"
    )
    
    tester.test_post(
        "/api/academy/agent_a/explain-visualization",
        "Get AI explanation for visualization",
        {
            "api_key": "test",
            "visualization_type": "revenue",
            "data": {},
            "personas": {}
        }
    )
    
    # ========================================
    # DATA LOADER ENDPOINTS (Used in AcademyAgentA.tsx)
    # ========================================
    print("\n\n" + "="*80)
    print("DATA LOADER ENDPOINTS")
    print("="*80)
    
    tester.test_get(
        "/api/academy/datasets",
        "List available datasets"
    )
    
    tester.test_post(
        "/api/academy/datasets/load",
        "Load a dataset",
        {"dataset_name": "v1"}
    )
    
    tester.test_get(
        "/api/academy/status",
        "Get dataset loading status"
    )
    
    # ========================================
    # MACRO DASHBOARD ENDPOINTS (Used in AcademyMacroDashboard.tsx)
    # ========================================
    print("\n\n" + "="*80)
    print("MACRO DASHBOARD ENDPOINTS")
    print("="*80)
    
    tester.test_get(
        "/api/academy/personas",
        "Get dynamic personas from Agent A"
    )
    
    tester.test_get(
        "/api/academy/macro-segments",
        "Get macro segments"
    )
    
    # Test micro segments for cluster 0 (will fail if no data)
    tester.test_get(
        "/api/academy/micro-segments/0",
        "Get micro segments for macro cluster 0"
    )
    
    # Test recommendations for sample customer
    tester.test_get(
        "/api/academy/recommendations/CUST_001/all",
        "Get all recommendations for customer"
    )
    
    # ========================================
    # AGENT B ENDPOINTS (Used in AcademyAgentB.tsx)
    # ========================================
    print("\n\n" + "="*80)
    print("AGENT B ENDPOINTS")
    print("="*80)
    
    tester.test_get(
        "/api/academy/agent_a/customers",
        "Get customers list for Agent B"
    )
    
    tester.test_post(
        "/api/academy/agent_b/execute",
        "Execute Agent B recommendations",
        {
            "customer_id": "CUST_001",
            "product_id": "PROD_001"
        }
    )
    
    tester.test_get(
        "/api/academy/agent_b/results",
        "Get Agent B results"
    )
    
    tester.test_get(
        "/api/academy/products",
        "Get products list"
    )
    
    # ========================================
    # RECOMMENDATION ENDPOINTS
    # ========================================
    print("\n\n" + "="*80)
    print("RECOMMENDATION ENDPOINTS")
    print("="*80)
    
    tester.test_get(
        "/api/academy/recommendations/CUST_001/similar",
        "Get similar products for customer"
    )
    
    tester.test_get(
        "/api/academy/recommendations/CUST_001/you-might-like",
        "Get 'You Might Like' recommendations"
    )
    
    tester.test_post(
        "/api/academy/recommendations/CUST_001/search",
        "Search products for recommendations",
        {"query": "tent"}
    )
    
    tester.test_get(
        "/api/academy/recommendations/new-visitor",
        "Get recommendations for new visitors"
    )
    
    # ========================================
    # CHROMADB ENDPOINTS
    # ========================================
    print("\n\n" + "="*80)
    print("CHROMADB ENDPOINTS")
    print("="*80)
    
    tester.test_get(
        "/api/academy/chromadb/status",
        "Get ChromaDB status"
    )
    
    tester.test_post(
        "/api/academy/chromadb/initialize",
        "Initialize ChromaDB",
        {}
    )
    
    # Print final summary
    tester.print_summary()
    
    # Additional instructions
    print("\nNEXT STEPS:")
    print("   1. If you see 404 errors for data-dependent endpoints, run Agent A first")
    print("   2. Check frontend browser console (F12) for any JavaScript errors")
    print("   3. Verify the frontend is running on http://localhost:3000")
    print("   4. Verify the backend is running on http://localhost:8002")
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

