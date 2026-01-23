"""
Quick Test Script for Micro Segments and Data Loader Fixes
Run this after starting the backend to verify all endpoints work correctly
"""

import requests
import json

API_BASE = "http://localhost:8002"

def test_endpoint(method, endpoint, description):
    """Test an API endpoint and print results"""
    print(f"\n{'='*80}")
    print(f"Testing: {description}")
    print(f"{method} {endpoint}")
    print('='*80)
    
    try:
        if method == "GET":
            response = requests.get(f"{API_BASE}{endpoint}")
        elif method == "POST":
            response = requests.post(f"{API_BASE}{endpoint}", json={})
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS")
            print(f"Response keys: {list(data.keys())}")
            return True, data
        else:
            print(f"❌ FAILED: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False, None

print("\n" + "="*80)
print("MICRO SEGMENTS & DATA LOADER API TESTS")
print("="*80)

# Test 1: Academy Datasets
print("\n📊 TEST 1: Academy Datasets Endpoint")
success, data = test_endpoint("GET", "/api/academy/datasets", "List Academy datasets")
if success and data:
    datasets = data.get('datasets', [])
    print(f"   Found {len(datasets)} datasets")
    for ds in datasets:
        print(f"   - {ds.get('name')}: {ds.get('customer_count')} customers")

# Test 2: Dataset View
print("\n📊 TEST 2: View Dataset Table")
success, data = test_endpoint("GET", "/api/academy/datasets/view/academy_sports_v1/customers", 
                               "View customers table")
if success and data:
    print(f"   Records returned: {data.get('preview_count')}")
    print(f"   Total records: {data.get('record_count')}")

# Test 3: Execute Agent A (to get macro segments)
print("\n🤖 TEST 3: Check Agent A Results")
success, data = test_endpoint("GET", "/api/academy/agent_a/results", "Get Agent A results")
agent_a_exists = success and data and data.get('results')
if agent_a_exists:
    print(f"   ✅ Agent A has been executed")
    personas = data.get('results', {}).get('personas', {})
    print(f"   Found {len(personas)} personas")
else:
    print(f"   ℹ️  Agent A not executed yet - run it first to test micro segments")

# Test 4: Macro Segments Endpoint
print("\n📈 TEST 4: Macro Segments Endpoint")
success, data = test_endpoint("GET", "/api/academy/macro-segments", "Get macro segments")
if success and data:
    segments = data.get('segments', [])
    print(f"   Found {len(segments)} macro segments")
    for seg in segments[:3]:  # Show first 3
        print(f"   - {seg.get('segment_name')}: {seg.get('size')} customers")

# Test 5: Micro Segments Creation (if Agent A was executed)
if agent_a_exists:
    print("\n🔬 TEST 5: Create Micro Segments")
    success, data = test_endpoint("POST", "/api/academy/micro-segments/0", 
                                   "Create micro segments for cluster 0")
    if success:
        result = data.get('result', {})
        micro_segs = result.get('micro_segments', [])
        print(f"   Created {len(micro_segs)} micro segments")
    
    # Test 6: Get Micro Segments
    print("\n🔬 TEST 6: Get Micro Segments")
    success, data = test_endpoint("GET", "/api/academy/micro-segments/0", 
                                   "Get micro segments for cluster 0")
    if success:
        result = data.get('result', {})
        micro_segs = result.get('micro_segments', {})
        if isinstance(micro_segs, dict):
            print(f"   ✅ Found {len(micro_segs)} micro segments (dict)")
            for seg_id, seg in list(micro_segs.items())[:2]:
                print(f"   - {seg.get('segment_name')}: {seg.get('size')} customers")
        elif isinstance(micro_segs, list):
            print(f"   ✅ Found {len(micro_segs)} micro segments (list)")
        else:
            print(f"   ⚠️  Unexpected type: {type(micro_segs)}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\n✅ If all tests show SUCCESS, the fixes are working correctly!")
print("\n📝 Next Steps:")
print("   1. Open frontend: http://localhost:5173")
print("   2. Go to Academy Sports → Agent A")
print("   3. Click 'Data Loader' tab to view datasets")
print("   4. Run Agent A clustering if not done")
print("   5. Click on a persona card to view micro segments")
print("\n" + "="*80 + "\n")
