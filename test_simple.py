"""Simple test for Phase 1 & Phase 2 (ASCII-only)"""
import requests

API_BASE = "http://localhost:8002"

print("\n" + "="*60)
print("PHASE 1 & PHASE 2 VALIDATION TEST")
print("="*60 + "\n")

# Test 1: ChromaDB Status
print("Test 1: ChromaDB Status")
try:
    response = requests.get(f"{API_BASE}/api/academy/chromadb/status")
    status = response.json()
    if status['success'] and status['status']['product_collection']['exists']:
        count = status['status']['product_collection']['count']
        print(f"  PASS: ChromaDB initialized with {count} products\n")
    else:
        print("  FAIL: ChromaDB not initialized\n")
except Exception as e:
    print(f"  ERROR: {e}\n")

# Test 2: Data Loading
print("Test 2: Data Loading")
try:
    response = requests.get(f"{API_BASE}/api/academy/datasets")
    datasets = response.json()
    if datasets['datasets']:
        count = len(datasets['datasets'])
        print(f"  PASS: Found {count} dataset(s)\n")
    else:
        print("  FAIL: No datasets found\n")
except Exception as e:
    print(f"  ERROR: {e}\n")

# Test 3: Macro Segmentation
print("Test 3: Macro Segmentation (this takes 10-15 seconds)")
try:
    # Load dataset
    requests.post(f"{API_BASE}/api/academy/datasets/load", json={"dataset_name": "academy_sports_v1"})
    
    # Run Agent A
    response = requests.post(f"{API_BASE}/api/academy/agent_a/execute", json={"n_clusters": 4})
    result = response.json()
    
    if result['success']:
        personas = result['result']['personas']
        print(f"  PASS: Created {len(personas)} macro segments\n")
    else:
        print("  FAIL: Macro segmentation failed\n")
except Exception as e:
    print(f"  ERROR: {e}\n")

# Test 4: Micro Segmentation
print("Test 4: Micro Segmentation")
try:
    response = requests.post(f"{API_BASE}/api/academy/micro-segments/0", params={"n_micro_segments": 4})
    result = response.json()
    
    if result['success']:
        micro_count = len(result['result']['micro_segments'])
        print(f"  PASS: Created {micro_count} micro segments\n")
    else:
        print("  FAIL: Micro segmentation failed\n")
except Exception as e:
    print(f"  ERROR: {e}\n")

# Test 5: Product Recommendations
print("Test 5: Product Recommendations")
try:
    customer_id = "CUST_00001"
    
    # Similar products
    response = requests.get(f"{API_BASE}/api/academy/recommendations/{customer_id}/similar")
    similar = response.json()
    
    # Search-based
    response = requests.post(
        f"{API_BASE}/api/academy/recommendations/{customer_id}/search",
        json={"search_term": "waterproof tent"}
    )
    search_results = response.json()
    
    if similar and search_results:
        print(f"  PASS: Similar products: {len(similar)}, Search results: {len(search_results)}\n")
    else:
        print("  FAIL: Recommendations failed\n")
except Exception as e:
    print(f"  ERROR: {e}\n")

print("="*60)
print("TESTS COMPLETE!")
print("="*60)
print("\nNext: Open http://localhost:5173/academy to test the UI")

