"""
Test all Academy Sports API endpoints
Requires backend to be running on localhost:8002
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8002"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=120)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=120)
        
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {method:4} {endpoint:50} [{response.status_code}] {description}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"     Error: {response.text[:100]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {method:4} {endpoint:50} [CONN] Backend not running!")
        return None
    except Exception as e:
        print(f"❌ {method:4} {endpoint:50} [ERR]  {str(e)[:50]}")
        return None

print("="*100)
print("TESTING ALL ACADEMY SPORTS API ENDPOINTS")
print("="*100)
print(f"Backend URL: {BASE_URL}")
print("="*100)

# Test 1: Dataset Management
print("\n📁 DATASET MANAGEMENT")
print("-"*100)
result = test_endpoint("GET", "/api/academy/datasets", description="List datasets")
result = test_endpoint("POST", "/api/academy/datasets/load", 
                      data={"dataset_name": "v1"}, 
                      description="Load V1 dataset")
result = test_endpoint("GET", "/api/academy/dataset-version", description="Get current version")
result = test_endpoint("GET", "/api/academy/status", description="Get system status")

# Test 2: Agent A - Macro Segmentation
print("\n🎯 AGENT A - MACRO SEGMENTATION")
print("-"*100)
result = test_endpoint("POST", "/api/academy/agent_a/execute", 
                      data={"n_clusters": 5, "gamma": 0.5}, 
                      description="Execute Agent A (5 clusters)")

if result and result.get('success'):
    print(f"     Generated {result.get('result', {}).get('n_clusters', 0)} personas")
    personas = result.get('result', {}).get('personas', {})
    for cluster_id, persona in list(personas.items())[:2]:
        print(f"     • {persona['persona_name']} ({persona['size']} customers)")

result = test_endpoint("GET", "/api/academy/agent_a/results", description="Get Agent A results")
if result and result.get('success'):
    personas = result.get('results', {}).get('personas', {})
    print(f"     Found {len(personas)} personas in results")

result = test_endpoint("GET", "/api/academy/personas", description="List all personas")
result = test_endpoint("GET", "/api/academy/macro-segments", description="Get macro segments")

# Test 3: Customer Insights
print("\n👥 CUSTOMER INSIGHTS")
print("-"*100)
result = test_endpoint("GET", "/api/academy/agent_a/customers?skip=0&limit=5", 
                      description="Get customers (paginated)")
if result and result.get('success'):
    customers = result.get('customers', [])
    print(f"     Retrieved {len(customers)} customers")
    if customers:
        customer_id = customers[0]['customer_id']
        print(f"     First customer: {customer_id}")
        
        # Test customer details
        result = test_endpoint("GET", f"/api/academy/agent_a/customer/{customer_id}", 
                             description=f"Get customer {customer_id} details")
        
        # Test customer explanation
        result = test_endpoint("POST", f"/api/academy/agent_a/customer/{customer_id}/explain",
                             data={}, 
                             description=f"Get AI explanation for {customer_id}")
        
        # Test customer recommendations
        result = test_endpoint("GET", f"/api/academy/agent_a/customer/{customer_id}/recommendations",
                             description=f"Get recommendations for {customer_id}")

result = test_endpoint("GET", "/api/academy/agent_a/export", description="Export persona assignments")

# Test 4: Visualization Explanations
print("\n📊 VISUALIZATION EXPLANATIONS")
print("-"*100)
viz_types = ['revenue', 'confidence', 'radar', 'seasonal', 'executive', 'validation', 'distribution']
for viz_type in viz_types:
    result = test_endpoint("POST", "/api/academy/agent_a/explain-visualization",
                         data={
                             "visualization_type": viz_type, 
                             "data": {}, 
                             "personas": {},
                             "api_key": None  # Will use system config
                         },
                         description=f"Explain {viz_type} visualization")

# Test 5: Agent B - Recommendations
print("\n🎁 AGENT B - PRODUCT RECOMMENDATIONS")
print("-"*100)
result = test_endpoint("POST", "/api/academy/agent_b/execute",
                      data={"customer_id": "CUST_0001"},
                      description="Execute Agent B")
result = test_endpoint("GET", "/api/academy/agent_b/results", description="Get Agent B results")
result = test_endpoint("GET", "/api/academy/products", description="List all products")

# Test 6: Micro Segmentation
print("\n🔬 MICRO SEGMENTATION")
print("-"*100)
result = test_endpoint("POST", "/api/academy/micro-segments/0",
                      data={"n_micro_segments": 3},
                      description="Create micro segments for cluster 0")
result = test_endpoint("GET", "/api/academy/micro-segments/0",
                      description="Get micro segments for cluster 0")

# Test 7: Product Recommendations (Various Types)
print("\n🛍️ PRODUCT RECOMMENDATIONS")
print("-"*100)
result = test_endpoint("GET", "/api/academy/recommendations/CUST_0001/similar",
                      description="Similar products (purchase history)")
result = test_endpoint("GET", "/api/academy/recommendations/CUST_0001/you-might-like",
                      description="You might like (micro segment)")
result = test_endpoint("POST", "/api/academy/recommendations/CUST_0001/search",
                      data={"search_term": "tent"},
                      description="Search-based recommendations")
result = test_endpoint("GET", "/api/academy/recommendations/CUST_0001/all",
                      description="All recommendations combined")
result = test_endpoint("GET", "/api/academy/recommendations/new-visitor",
                      description="New visitor recommendations")

# Test 8: ChromaDB Management
print("\n🗄️ CHROMADB MANAGEMENT")
print("-"*100)
result = test_endpoint("GET", "/api/academy/chromadb/status", description="Get ChromaDB status")
# Note: Don't initialize ChromaDB in test as it takes time
# result = test_endpoint("POST", "/api/academy/chromadb/initialize", description="Initialize ChromaDB")

# Summary
print("\n" + "="*100)
print("TEST SUMMARY")
print("="*100)
print("All endpoints tested. Check for ❌ marks above for any failures.")
print("="*100)

