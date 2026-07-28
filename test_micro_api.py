"""
Test micro segments API directly to see response structure
"""
import requests
import json

API_BASE = "http://localhost:8002"

# Test cluster 0
response = requests.get(f"{API_BASE}/api/academy/micro-segments/0")

print("="*80)
print("GET /api/academy/micro-segments/0")
print("="*80)
print(f"Status: {response.status_code}")
print("\nResponse JSON:")
print(json.dumps(response.json(), indent=2))

# Check the structure
data = response.json()
print("\n" + "="*80)
print("DATA STRUCTURE ANALYSIS")
print("="*80)
print(f"Has 'success': {('success' in data)}")
print(f"Has 'result': {('result' in data)}")

if 'result' in data:
    result = data['result']
    print(f"\nresult type: {type(result)}")
    print(f"result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
    
    if isinstance(result, dict) and 'micro_segments' in result:
        micro_segs = result['micro_segments']
        print(f"\nmicro_segments type: {type(micro_segs)}")
        print(f"micro_segments length: {len(micro_segs) if isinstance(micro_segs, list) else 'not a list'}")
        
        if isinstance(micro_segs, list) and len(micro_segs) > 0:
            print(f"\nFirst micro segment:")
            print(json.dumps(micro_segs[0], indent=2))
        else:
            print("\n❌ micro_segments is empty or not a list!")
    else:
        print("\n❌ No 'micro_segments' in result!")
else:
    print("\n❌ No 'result' key in response!")

print("\n" + "="*80)


