"""
Quick Test Script for Phase 1 & Phase 2
Run this to validate the complete implementation
"""

import requests
import time
import json
from colorama import init, Fore, Style

init(autoreset=True)

API_BASE = "http://localhost:8002"

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}{text}")
    print(f"{Fore.CYAN}{'='*70}\n")

def print_success(text):
    print(f"{Fore.GREEN}✓ {text}")

def print_error(text):
    print(f"{Fore.RED}✗ {text}")

def print_info(text):
    print(f"{Fore.YELLOW}ℹ {text}")

def test_chromadb_initialization():
    """Test ChromaDB initialization"""
    print_header("TEST 1: ChromaDB Initialization")
    
    try:
        # Check status first
        response = requests.get(f"{API_BASE}/api/academy/chromadb/status")
        status = response.json()
        
        if status['success'] and status['status']['product_collection']['exists']:
            print_success(f"ChromaDB already initialized with {status['status']['product_collection']['count']} products")
            return True
        
        # Initialize
        print_info("Initializing ChromaDB... (this may take 30-60 seconds)")
        response = requests.post(f"{API_BASE}/api/academy/chromadb/initialize")
        result = response.json()
        
        if result['success']:
            product_init = result['result']['product_initialization']
            print_success(f"Initialized {product_init['product_count']} products")
            print_success(f"Time taken: {product_init['elapsed_time']}s")
            return True
        else:
            print_error("ChromaDB initialization failed")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_data_loading():
    """Test data loading"""
    print_header("TEST 2: Data Loading")
    
    try:
        response = requests.get(f"{API_BASE}/api/academy/datasets")
        datasets = response.json()
        
        if datasets['datasets']:
            print_success(f"Found {len(datasets['datasets'])} dataset(s)")
            for ds in datasets['datasets']:
                print_info(f"  - {ds['name']}: {ds['customer_count']} customers, {ds['product_count']} products")
            return True
        else:
            print_error("No datasets found")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_macro_segmentation():
    """Test macro segmentation"""
    print_header("TEST 3: Macro Segmentation")
    
    try:
        # Load dataset first
        response = requests.post(
            f"{API_BASE}/api/academy/datasets/load",
            json={"dataset_name": "academy_sports_v1"}
        )
        
        if response.ok:
            print_success("Dataset loaded")
        
        # Run Agent A
        print_info("Running macro segmentation... (this may take 10-15 seconds)")
        response = requests.post(
            f"{API_BASE}/api/academy/agent_a/execute",
            json={"n_clusters": 4}
        )
        result = response.json()
        
        if result['success']:
            personas = result['result']['personas']
            print_success(f"Created {len(personas)} macro segments")
            
            for persona_id, persona_data in personas.items():
                print_info(f"  - {persona_data['persona_name']}: {persona_data['size']} customers (${persona_data['total_revenue']:.2f})")
            
            return True, personas
        else:
            print_error("Macro segmentation failed")
            return False, None
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False, None

def test_micro_segmentation(macro_segment_id):
    """Test micro segmentation for a macro segment"""
    print_header(f"TEST 4: Micro Segmentation (Macro Segment {macro_segment_id})")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/academy/micro-segments/{macro_segment_id}",
            params={"n_micro_segments": 4}
        )
        result = response.json()
        
        if result['success']:
            micro_segments = result['result']['micro_segments']
            print_success(f"Created {len(micro_segments)} micro segments")
            
            for micro_id, micro_data in micro_segments.items():
                print_info(f"  - {micro_data['segment_name']}: {micro_data['size']} customers, {micro_data['ltv_tier']} tier")
            
            return True, micro_segments
        else:
            print_error("Micro segmentation failed")
            return False, None
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False, None

def test_recommendations(customer_id):
    """Test product recommendations"""
    print_header(f"TEST 5: Product Recommendations (Customer {customer_id})")
    
    try:
        # Test similar products
        response = requests.get(f"{API_BASE}/api/academy/recommendations/{customer_id}/similar")
        similar = response.json()
        
        if similar:
            print_success(f"Similar Products: {len(similar)} recommendations")
            if similar:
                print_info(f"  - Top: {similar[0]['product_name']} (${similar[0]['price']})")
        
        # Test search-based
        response = requests.post(
            f"{API_BASE}/api/academy/recommendations/{customer_id}/search",
            json={"search_term": "waterproof tent"}
        )
        search_results = response.json()
        
        if search_results:
            print_success(f"Search Results: {len(search_results)} recommendations")
            if search_results:
                print_info(f"  - Top: {search_results[0]['product_name']} (${search_results[0]['price']})")
        
        # Test new visitor
        response = requests.get(f"{API_BASE}/api/academy/recommendations/new-visitor")
        new_visitor = response.json()
        
        if new_visitor:
            print_success(f"New Visitor Recommendations: {len(new_visitor['top_selling'])} products")
        
        return True
        
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print_header("🚀 PHASE 1 & PHASE 2 VALIDATION TEST SUITE")
    
    print_info("Testing against API at: " + API_BASE)
    print_info("Make sure backend is running: py -3.10 api/main_unified_chromadb.py\n")
    
    time.sleep(1)
    
    # Test 1: ChromaDB
    chromadb_ok = test_chromadb_initialization()
    time.sleep(1)
    
    # Test 2: Data Loading
    data_ok = test_data_loading()
    time.sleep(1)
    
    # Test 3: Macro Segmentation
    macro_ok, personas = test_macro_segmentation()
    time.sleep(1)
    
    # Test 4: Micro Segmentation
    micro_ok = False
    if macro_ok and personas:
        first_macro_id = list(personas.keys())[0]
        micro_ok, micro_segments = test_micro_segmentation(first_macro_id)
        time.sleep(1)
    
    # Test 5: Recommendations
    recs_ok = False
    if macro_ok:
        # Use a test customer
        test_customer = "CUST_00001"
        recs_ok = test_recommendations(test_customer)
    
    # Summary
    print_header("📊 TEST SUMMARY")
    
    tests = [
        ("ChromaDB Initialization", chromadb_ok),
        ("Data Loading", data_ok),
        ("Macro Segmentation", macro_ok),
        ("Micro Segmentation", micro_ok),
        ("Product Recommendations", recs_ok)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Fore.CYAN}Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{Fore.GREEN}{'='*70}")
        print(f"{Fore.GREEN}🎉 ALL TESTS PASSED! Phase 1 & 2 implementation is working! 🎉")
        print(f"{Fore.GREEN}{'='*70}\n")
        print(f"{Fore.CYAN}Next steps:")
        print(f"  1. Open frontend: http://localhost:5173/academy")
        print(f"  2. Navigate through: Data → Macro → Micro → Recommendations")
        print(f"  3. Review PHASE1_PHASE2_COMPLETE_GUIDE.md for full documentation")
    else:
        print(f"\n{Fore.RED}Some tests failed. Check the errors above.")
        print(f"{Fore.YELLOW}Make sure:")
        print(f"  1. Backend is running on port 8002")
        print(f"  2. Data files exist in data/preloaded/academy_sports/")
        print(f"  3. Together AI API key is set (for ChromaDB)")

if __name__ == "__main__":
    main()

